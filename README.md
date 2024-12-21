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
6. *proc.c* : Added important functions and strace functionality implementation code.
7. *proc.h* : Added tracing flag in procedure function.
8. *strace.c* : Containing Code for strace implementation.
9. *stracefork.c*: File for child fork testing.
10. *syscall.c*: Added support for tracing specific system calls with various flags (-e, -s, -f) and combinations of these.
12. *syscall.h*: Introduced new system call definitions for the tracing functionality.
13. *sh.c*: Modified to parse and handle new tracing commands and flags for strace.
14. *user.h*: Added strace definitions.
15. *usys.S* : Added System Calls.
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
make qemu-nox


### How to run strace commands
strace on
strace off
strace dump
strace run echo hello
stracefork
strace -e echo hello
strace -s
strace -f
strace -s -e write
strace -f -e write
