# BetterLoggerFrame
<img src="https://img.shields.io/badge/Author-Xu.Cao-lightgreen" alt="Author" />
  
system : Ubuntu 22.04 LTS  
kernel : 5.15.0-53-generic  
tool : BCC  
Version: v0.2.1.221120_build_b3_Xu.C  
  
## Note
This project ask for conditions as follows:  
- Clear Path Structure: You need put C file with ebpf code into "src/" and directory "ctl/" is reserved.  
- Modules Thought: You can see ".c" as a module, and you plug that in the whole program by modify the "plugin.json". 
You can modify it referring the example "plugin.json".  
  
you can use it by running `./loader.py` and then `sudo ./ebpf.py`.
  
## Original thought
This project is mainly to make a logger frame which will provide high-quality logs. I want this frame to have these
 features as follows:  
  
### Natively
I want the framework to use built-in methods as much as possible to reduce dependencies on external libraries.
### Easier to use
I hope that this framework can user-friendly and do something automatically as much as possible.
### Pluggable
I hope that this framework can be pluggable and be enhanced easily in the future.
