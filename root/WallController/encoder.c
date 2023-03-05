#include <fcntl.h>
#include <poll.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/epoll.h>
#include <linux/gpio.h>
#include <linux/interrupt.h>

#define DIR_NONE 0x0
// Clockwise step.
#define DIR_CW 0x10
// Anti-clockwise step.
#define DIR_CCW 0x20

#define R_START 0x0
#define R_CW_FINAL 0x1
#define R_CW_BEGIN 0x2
#define R_CW_NEXT 0x3
#define R_CCW_BEGIN 0x4
#define R_CCW_FINAL 0x5
#define R_CCW_NEXT 0x6

int main(void) {
    int state = R_START;
    const unsigned char ttable[7][4] = {
        // R_START
        {R_START,    R_CW_BEGIN,  R_CCW_BEGIN, R_START},
        // R_CW_FINAL
        {R_CW_NEXT,  R_START,     R_CW_FINAL,  R_START | DIR_CW},
        // R_CW_BEGIN
        {R_CW_NEXT,  R_CW_BEGIN,  R_START,     R_START},
        // R_CW_NEXT
        {R_CW_NEXT,  R_CW_BEGIN,  R_CW_FINAL,  R_START},
        // R_CCW_BEGIN
        {R_CCW_NEXT, R_START,     R_CCW_BEGIN, R_START},
        // R_CCW_FINAL
        {R_CCW_NEXT, R_CCW_FINAL, R_START,     R_START | DIR_CCW},
        // R_CCW_NEXT
        {R_CCW_NEXT, R_CCW_FINAL, R_CCW_BEGIN, R_START},
        };
    int left_file;
    int right_file;
    char left_buf[2];
    char right_buf[2];

    // Export the Left GPIO pin
    FILE *export_file_left = fopen("/sys/class/gpio/export", "w");
    fprintf(export_file_left, "502");
    fclose(export_file_left);
    
    // Export the Right GPIO pin
    FILE *export_file_right = fopen("/sys/class/gpio/export", "w");
    fprintf(export_file_right, "501");
    fclose(export_file_right);

    // Set the direction of the left pin to input
    FILE *direction_file_left = fopen("/sys/class/gpio/gpio502/direction", "w");
    fprintf(direction_file_left, "in");
    fclose(direction_file_left);

    // Set the direction of the right pin to input
    FILE *direction_file_right = fopen("/sys/class/gpio/gpio501/direction", "w");
    fprintf(direction_file_right, "in");
    fclose(direction_file_right);

    // Set the edge trigger type to rising edge
    FILE *edge_file_left = fopen("/sys/class/gpio/gpio502/edge", "w");
    fprintf(edge_file_left, "both");
    fclose(edge_file_left);

    // Set the edge trigger type to rising edge
    FILE *edge_file_right = fopen("/sys/class/gpio/gpio501/edge", "w");
    fprintf(edge_file_right, "both");
    fclose(edge_file_right);

    // Open the value file for the right GPIO pin
    left_file = open("/sys/class/gpio/gpio502/value", O_RDONLY);

    // Open the value file for the left GPIO pin
    right_file = open("/sys/class/gpio/gpio501/value", O_RDONLY);

    // Create an epoll instance
    int epoll_fd = epoll_create(1);
    if (epoll_fd == -1) {
        perror("epoll_create");
        return 1;
    }

    // Add the value file to the epoll instance
    struct epoll_event left_event = { .events = EPOLLET };
    left_event.data.fd = left_file;
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, left_file, &left_event) == -1) {
        perror("epoll_ctl");
        return 1;
    }
    struct epoll_event right_event = { .events = EPOLLET };
    right_event.data.fd = right_file;
    if (epoll_ctl(epoll_fd, EPOLL_CTL_ADD, right_file, &left_event) == -1) {
        perror("epoll_ctl");
        return 1;
    }

    // Main loop
    while (1) {
        int nfds_left = epoll_wait(epoll_fd, &left_event, 1, -1);
        if (nfds_left == -1) {
            perror("epoll_wait");
            return 1;
        }

        // Handle the interrupt
        lseek(left_file, 0, SEEK_SET);
        lseek(right_file, 0, SEEK_SET);
        read(left_file, left_buf, sizeof(left_buf));
        read(right_file, right_buf, sizeof(right_buf));
        //printf("Interrupt detected on GPIO 502 with value %c\n", left_buf[0]);
        //printf("Interrupt detected on GPIO 501 with value %c\n", right_buf[0]);
        unsigned char pinstate = ( ((int)left_buf[0]-48) << 1) | ((int)(right_buf[0]-48));
        //printf("%d\n",(int)left_buf[0]-48 << 1); 
        //printf("%d\n",(int)right_buf[0]-48);
        state = ttable[state & 0xf][pinstate];
        //printf("[%d][%d]\n",(state & 0xf),pinstate);
        //printf("%d\n",state & 0x30);
        //printf("%d\n",state);
        if ((state & 0x30) == DIR_CCW){
            printf("counterclockwise\n");
        }else if ((state & 0x30) == DIR_CW){
            printf("clockwise\n");
        }
    }

    // Unexport the left GPIO pin
    FILE *unexport_file_left = fopen("/sys/class/gpio/unexport", "w");
    fprintf(unexport_file_left, "502");
    fclose(unexport_file_left);

    // Unexport the right GPIO pin
    FILE *unexport_file_right = fopen("/sys/class/gpio/unexport", "w");
    fprintf(unexport_file_right, "501");
    fclose(unexport_file_right);

    return 0;
}

