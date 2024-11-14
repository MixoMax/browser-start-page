#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int levenshtein_distance(const char *s1, const char *s2) {
    const int del_cost = 1;
    const int ins_cost = 1;
    const int sub_cost = 1;


    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);

    int *prev_row = (int *)malloc((len2 + 1) * sizeof(int));
    int *curr_row = (int *)malloc((len2 + 1) * sizeof(int));

    for (size_t j = 0; j <= len2; j++) {
        prev_row[j] = j * ins_cost;
    }

    for (size_t i = 1; i <= len1; i++) {
        curr_row[0] = i * del_cost;
        for (size_t j = 1; j <= len2; j++) {
            int cost = (s1[i - 1] == s2[j - 1]) ? 0 : sub_cost;
            int insert = curr_row[j - 1] + ins_cost;
            int delete = prev_row[j] + del_cost;
            int substitute = prev_row[j - 1] + cost;

            int min = insert < delete ? insert : delete;
            curr_row[j] = min < substitute ? min : substitute;
        }
        int *temp = prev_row;
        prev_row = curr_row;
        curr_row = temp;
    }

    int distance = prev_row[len2];
    free(prev_row);
    free(curr_row);
    return distance;
}

int main() {
    const char *s1 = "kitten";
    const char *s2 = "sitting";
    int distance = levenshtein_distance(s1, s2);
    printf("Levenshtein distance between %s and %s is %d\n", s1, s2, distance);
    return 0;
}