# Complete-Python-Bootcamp



### Create Python Enviroment  
```bash
# this would create the enviroment under  C:\Users\Dell\.conda\envs\pyEnv3.12 ; If we use -p option then 
# that  would create the enviroment under the current folder example : conda create -p pyEnv3.12 python==3.12
conda create --name pyEnv3.12 python==3.12 

# TO activate the specific env 
conda activate pyEnv3.12

# List available enviroments 
conda envs list

```

### Set VSCODDE interpreter 

```Win32
Ctrl + Shift + P + Select the path  C:\Users\Dell\.conda\envs\pyEnv3.12
```

### Installing ipykernel
```bash
#Before installing ensure the correct name of the python Env. is getting displayed within ( )
(pyEnv3.12) E:\GitHub\Python-Dev\PythonBootcamp> pip install ipykernel

```