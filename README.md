# aws-lambda restart EC2 docker containers

This script is used to detach EC2 from ELB if on certain condition(CPU usage >90%) and invoke a script to restart containers. Re registering the EC2 to ELB is not written here, as, aws lamda runs only for 5 min.
