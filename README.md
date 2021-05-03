#PhoenixGeoPy

## What does this project do?

This project enables users to parse and handle Phoenix Geophysics binary time series from the MTU-5C family of receivers.

## Why is this project useful?

This project allows the geophysical community to work with native Phoenix time series from the MTU-5C family of systems and create their own code, allowing them to solve the next geophysical data challenge!

## How do I get started?

### Installing the necessary packages

First you will need to install Python3 in your system if you don't have it already. You can find Python3 for different oeprating systems. In Windows we recommend using Cygwin or MSYS2.

For now, most of our documentation will be tested in a Linux computer, but if you know your way around python, or if you Google a little, you will find how to do the same in your system.

In a modern Debian-based Linux system you can install Python3 by typing in a console:

```bash
sudo apt install python3
```

You will also need to install a few other python3 libraries if you don't have then already. Note that matplotlib is only needed to run the examples, and not by the PhoenixGeoPy library itself. If you are not planning to run the examples, you can ommit installing python3-matplotlib

```bash
sudo apt install python3-numpy python3-matplotlib
```

### Now the fun can start

Clone the project. Then in a console that has access to python3, change directories to the location where you cloned this PhoenixGeoPy project. You should see this README.md file in that directory.

Once there, you will need to define this directory as a directory that has libraies that python3 can import. This will be effective for this session of the console. You only need to do this once on that console, while it remains open.

The following command should define your cloned project as a path where python will look for libraries for a bash console. You can easily find a bash-compatible console commonly in Linux or Mac, and in Windows you can use an MSYS2 or Cygwin running bash console.

```bash
PYTHONPATH=$(pwd):$PYTHONPATH
```

Remember, while you keep that console open, you only need to run this command above once.

Now that python knows how to find your newly downloaded library, change directories to the "Examples" folder

```bash
cd Examples
```

And now, you are ready to run the example:

```bash
python3 NativeSampleReader.py
````

You should see a window with a plot of a sine wave. The console where you ran the commands above will present an interactive prompt that will let you navigate through the time series, or to exit the program.

If you need to read data from Phoenix time series files, you can make a copy of the example and substitute the code that plots the data by your own code. Easy!


## What is the license type for this project?
[MIT](https://choosealicense.com/licenses/mit/)

## How do I contribute?

You are welcome to send pull requests if you find a severe bug. For major changes, please open an issue first to discuss what you would like to change.

## Coding style

We loosely adhered to [PEP8](https://www.python.org/dev/peps/pep-0008/) coding style whenever it was possible. As a change, we allow for 120 characters long lines though.

We encourage you to keep the same style format

## Where can I get more help, if I need it?

This project comes with no technical support or warranty. You can ask the community in github. For this to work, you should also be willing to help the community. Please become an active participant of the project by answering questions of other users!

