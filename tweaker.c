/* Small tool to modify scale/translate matrix of PES models */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
    char filename[512];
    memset(filename, 0, sizeof(filename));
    if (argc>1) {
        strncpy(filename, argv[1], sizeof(filename));
    }
    else {
        printf("Enter .model filename: ");
        size_t linecap = 0;
        fgets(filename, sizeof(filename), stdin);
        if (filename[strlen(filename)-1]=='\n') filename[strlen(filename)-1]='\0';
        if (filename[strlen(filename)-1]=='\r') filename[strlen(filename)-1]='\0';
    }
    printf("MODEL: %s\n", filename);

    int off1, off2, matrix_off;
    float matrix[3][4];

    FILE *f = fopen(filename,"rb");
    if (!f) {
        printf("ERROR: unable to read file: %s\n", filename);
        return 1;
    }

    char header[0x18] = "MODEL\0\0\0\x10\0\0\0\0\0\x13\0\x09\0\0\0\0\0\0\0";
    char hdr[0x18];
    fread(hdr, sizeof(hdr), 1, f);
    if (memcmp(header, hdr, sizeof(header))!=0) {
        printf("ERROR: File format of %s is not supported.\n", filename);
        printf("Only uncompressed MODEL files from PC game are supported.\n");
        return 1;
    }

    int data_pattern[7] = { 0x10, 1, 0x0c, 0x02, 0, 7, 1 };
    int data[7] = { 0, 0, 0, 0, 0, 0, 0 };

    fseek(f, 0x50+12, SEEK_SET);
    fread(&off1, 4, 1, f);
    fseek(f, 0x50+off1, SEEK_SET);
    fread(data, 4, 7, f);
    data_pattern[4] = data[4];
    if (memcmp(data_pattern, data, sizeof(data_pattern))!=0) {
        printf("WARN: This MODEL does not have a scale/translate matrix\n");
        printf("Nothing to do, exiting.\n");
        return 2;
    }

    off2 = data[4];
    fseek(f, 0x50+off1+off2, SEEK_SET);
    matrix_off = ftell(f);
    fread(&matrix, 4, 12, f);
    fclose(f);

    printf("Current scale vector: (x=%0.3f, z=%0.3f, y=%0.3f)\n",
        matrix[0][0], matrix[1][1], matrix[2][2]);
    printf("Current translate vector: (x=%0.3f, z=%0.3f, y=%0.3f)\n",
        matrix[0][3], matrix[1][3], matrix[2][3]);

    char ans[10];

    printf("Change scale vector? (y/N): ");
    memset(ans, 0, sizeof(ans));
    fgets(ans, sizeof(ans), stdin);
    if (ans[0] == 'y' || ans[0] == 'Y') {
        printf("x: "); fscanf(stdin, "%f", &matrix[0][0]);
        printf("z: "); fscanf(stdin, "%f", &matrix[1][1]);
        printf("y: "); fscanf(stdin, "%f", &matrix[2][2]);
        fgets(ans, sizeof(ans), stdin);

        FILE *f = fopen(filename,"r+b");
        if (!f) {
            printf("ERROR: unable to write file: %s\n", filename);
        }
        fseek(f, matrix_off, SEEK_SET);
        fwrite(&matrix, 4, 12, f);
        fclose(f);
        printf("Scale vector changed.\n");
    }

    printf("Change translate vector? (y/N): ");
    memset(ans, 0, sizeof(ans));
    fgets(ans, sizeof(ans), stdin);
    if (ans[0] == 'y' || ans[0] == 'Y') {
        printf("x: "); fscanf(stdin, "%f", &matrix[0][3]);
        printf("z: "); fscanf(stdin, "%f", &matrix[1][3]);
        printf("y: "); fscanf(stdin, "%f", &matrix[2][3]);
        fgets(ans, sizeof(ans), stdin);

        FILE *f = fopen(filename,"r+b");
        if (!f) {
            printf("ERROR: unable to write file: %s\n", filename);
        }
        fseek(f, matrix_off, SEEK_SET);
        fwrite(&matrix, 4, 12, f);
        fclose(f);
        printf("Translate vector changed.\n");
    }

    return 0;
}
