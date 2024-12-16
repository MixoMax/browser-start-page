const token = atob("Z3NrXzZVSXA3RjdUcDFSa1hydktZSzgwV0dkeWIzRlkxazg1UTg3SzRMSHpkWk43cVF0RlhUc1Y");

// Insert ai summary to duckduckgo search results
const ai_summary = document.createElement("div");
ai_summary.style = "color: var(--theme-col-txt-snippet); padding: 10px; margin: 10px; border: 1px solid var(--theme-col-border); border-radius: 5px;";
ai_summary.innerHTML = "<div class='ai-summary'><h2>AI Summary</h2><p>AI summary is here</p></div>";

// make <b> tags way more visible
const style = document.createElement("style");
style.innerHTML = ".ai-summary b { font-weight: bold; font-size: 3em; }";
document.head.appendChild(style);


// insert ai summary to the search results
// find <div data-testid="web-vertical"> and insert ai_summary as the second child
const web_vertical = document.querySelector('div[data-testid="web-vertical"]');
web_vertical.insertBefore(ai_summary, web_vertical.children[1]);


function get_ai_summary() {
    const t_start = performance.now();

    const search_query = document.getElementById("search_form_input").value;

    // get the links and their descriptions
    const result_divs = document.querySelectorAll('article[data-testid="result"]');
    const links = [];
    const descriptions = [];
    result_divs.forEach(div => {
        const link = div.querySelector('a[data-testid="result-extras-url-link"]').href;
        const description = div.querySelectorAll('div[data-result="snippet"] div span span')[div.querySelectorAll('div[data-result="snippet"] div span span').length - 1].textContent;
        links.push(link);
        descriptions.push(description);
    });

    // fetch the first link and get the full text
    var website_text = "";
    fetch(links[0])
    .then(response => response.text())
    .then(website_data => {
        const parser = new DOMParser();
        const html = parser.parseFromString(website_data, 'text/html');
        const paragraphs = html.querySelectorAll('p');
        const max_chars = 1000;
        paragraphs.forEach(p => {
            if (website_text.length < max_chars) {
                website_text += p.textContent + " ";
            }
        });
    

        // create the text to send to the AI model

        var text = "Please provide a Summary of the search results to answer the users question: " + search_query + "\n";
        text += "Please provide the shortest possible answer that answers the question.\n";
        text += "Highlight important information and numbers in the answer by using bold (**).\n";
        text += "Only highlight the very most important information and figures.\n";
        text += "Do not include any unnecessary information and please keep the summary to only a maximum of 2 sentences unless the user asks you to list X number of things.\n";
        text += "If the users question can be answerd in a single Figure, please only provide the figure.\n";
        text += "If the users question can be answered in a single word, please only provide the word.\n";
        text += "If you include a link in the answer, make sure that either the whole link is bold or none of it is bold.\n";
        text += "Always answer in English.\n";

        text += "Website Results: \n";
        for (var i = 0; i < links.length; i++) {
            text += "url: " + links[i] + "\n";


            if (i == 0) {
                text += "Website Text: \n";
                text += website_text + "\n";
            } else {
                text += "Website Summary: \n";
                text += descriptions[i] + "\n";
            }

            text += "\n";
        }
        text += "Make sure to answer in English only.\n";


        // send the text to the AI model
        console.log("test");
        fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
                "Content-Security-Policy": 'default-src \'self\'; connect-src https://api.groq.com',
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
            },
            body: JSON.stringify({
                "messages": [
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "model": "llama-3.1-8b-instant",
                "temperature": 1,
                "max_tokens": 1024,
                "top_p": 1,
                "stream": false,
                "stop": null
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            const ai_summary = document.querySelector('.ai-summary');
            var ai_text = data.choices[0].message.content;
            
            is_bold = false;
            ai_text = ai_text.replace(/\*\*/g, function(match) {
                is_bold = !is_bold;
                return is_bold ? "<b>" : "</b>";
            });

            // parse for https:// and make it a link
            ai_text = ai_text.replace(/(https:\/\/[^\s]+)/g, '<a href="$1">$1</a>');



            ai_summary.innerHTML = "<h2>AI Summary</h2><p>" + ai_text + "</p>";

            // get <a> in ai_summary and fix them
            const ai_links = ai_summary.querySelectorAll('a');
            ai_links.forEach(link => {
                link.target = "_blank";
                link.style = "color: var(--theme-col-txt-snippet);";
                link.href = link.href.replace("<b>", "").replace("</b>", "").replace("%3C/b%3E", "").replace("%3C%2Fb%3E", "");
                console.log(link.href);
            });

            const t_end = performance.now();
            console.log("AI Summary took " + (t_end - t_start) + " milliseconds.");
        })
        .catch(error => {
            console.error('Error:', error);
            console.log(data)
        });
    });

}
get_ai_summary();