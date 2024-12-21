# xv6 Strace Project 

## *Overview*
This repository contains an implementation of strace functionality in the xv6 operating system. The strace utility is used to trace system calls made by a program during its execution. This README provides instructions for setting up the project, compiling xv6, and running the OS with the strace functionality.

---
## How This xv6 Implementation Differs from the Original

### Modified/Added Files
1. *defs.h* : Added system call and functions definitions.
2. *exec.c* : Edited exec function to include proc field.
3. *lapic.c* : Added lapicid function.
4. *MAKEFILE* : Added necessary things in MAKEFILE.
5. *params.h* : Added a new variable to store number maximum system calls to be stored in buffer.
6. *kernel/syscall.c*: Added support for tracing specific system calls with various flags (-e, -s, -f) and combinations of these.
7. *kernel/syscall.h*: Introduced new system call definitions for the tracing functionality.
8. *user/sh.c*: Modified to parse and handle new tracing commands and flags for strace.
9. *kernel/fs.c*: Altered the writei() function to suppress command output when strace is active, enabling cleaner tracing output.5.  *kernel/trap.h*: Global variable definitions.
10. *Makefile*: Updated to include new dependencies for the custom tracing functionality.
11. *sTest.c*: Trace child process implementation.
12. *memoryleak.c*: Application of memory leak in xv6. 
13. *memleak2.c*: Application of memory leak into file memleakfile.txt.
---

## How to Run the Program


## *Setup Instructions*

bash
sudo apt update
sudo apt install -y build-essential qemu qemu-system-x86

# Compiling and Running xv6

## Compiling xv6

### 1. Build xv6
If you are using the class VM or a compatible Linux environment, you can compile xv6 by running the following command in the project directory:

bash
cd STRACE
make clean
make
make qemu

OR
bash
make clean && make xv6.img && make qemu


### How to run strace commands
bash
strace on
strace off
strace dump
strace run echo hello
./sTest
strace -e echo hello
strace -s
strace -f
strace -s -e write
strace -f -e write
./memoryleak
strace ./memleak2 &> memleakfile.txt
