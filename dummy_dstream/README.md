# Example for dummies

This directory contains some dummy pubs projects one can use to exercise the basics.
We will register two fake projects and see how it runs within `PUBS`.
One project creates an empty file, and another project copies that file to another directory.
They will be executed by `PUBS` daemon.

### Preparation

We assume we have a "DummyRun" primary run/subrun database table filled with some runs and sub-runs. 
We further assume that this table solely exists for this exercise purpose (i.e. we will mess with its contents).
If you do not have such table, you can make one:
```
cd $PUB_TOP_DIR
sbin/create_runtable DummyRun
```
Let's fill with 100 runs each with 100 subruns
```
sbin/refill_runtable --name DummyRun --nruns 100 --nsubruns 100
```

Next, we create directories projects want to create/transfer files.
We could write projects such that it creates a new directory automatically. 
But we decided projects should rather fail if specified directory does not exists instead of being "smart" to create it by itself.
```
mkdir dummy_daq_out
mkdir dummy_daq_storage
```
One project will make an empty file in `dummy_daq_out`, and another one copies it to `dummy_daq_storage`.

### Exercise
OK let's start up the daemon.
```
daemon.sh start
```
You can open another terminal to monitor the log
```
(open new terminal, go to pubs directory)
tail -f log/proc_daemon.log
```

You should see the daemon running.
Next, we register projects with a configuration file.
```
sbin/register_project dummy_dstream/cfg/dummy_project.cfg
```
You can take a look at the content of the config file anytime to get the feeling. 
Then also take a look at executed scripts so that you know how to parse configuration parameters  you define for your own scripts.

Now, go take a look at `proc_daemon.log` in the other window.
You should see no project running. Sad... but that's because `dummy_project.cfg` by default disabled projects from being executed.
We can re-enable it either by modifying `dummy_project.cfg` and running `register_project`, or simply by this
```
sbin/pmod_enable dummy_daq 1
```
... where the 1st argument is the `project name` and the 2nd argument is the flag `1=enable` and  `0=disable`.

Now take a look at `proc_daemon.log`. You should see `dummy_daq` running.
After you confirm that in the log, check
```
ls dummy_daq_out
```
and you should find some files there.

So let's next enable `dummy_xfer`, the other project. I tell you a trick of `pmod_enable` script here.
Sometimes it's annoying to answer `[yes/no]` on the prompt. If you know what you are doing, you can give the 3rd argument `0` to skip the prompt.
```
sbin/pmod_enable dummy_xfer 1 0
```

Go check if you see the project running in `proc_daemon.log` and files appearing under `dummy_daq_storage`!

