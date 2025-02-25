## Introduction

### What this?

This is a very simple updater that allows you to customize everything very easily.

### What can it do?

Package distribution, game mod installation, file synchronization and more, the only limit is your imagination!

## Features

Command actions marked with versions, no need to calculate md5, etc.

Support file download and deletion

Allow installation scripts to run

Multi-version control, allowing control of updated versions (using the SemVer standard）

Use one of the newest configuration file formats: toml

## How to use?

### For Client:

You need to put updater.exe and package.toml in the package.

### For Server:

Prepare a server or use GitHub directly for file distribution, anything that supports file downloads will do.

#### From the directory structure, it should look like this:

~~~ tree
{baseURL}
| - packages.toml
| - 1.0.0
  | - package.toml
  | - example1.txt
  | - dict
    | - example2.txt
| - 1.0.1
| - 1.1.0 Beta
| - <more version>
  | - etc.
~~~

#### packages.toml 

Declares the versions currently provided by all servers and the recommended version

~~~ toml
[common]
recommand = "1.0.1"
versions = ["1.0.0", "1.0.1", "1.1.0 Beta"]
~~~

Note that the version number must be in the format x.y.z and if there is a subsequent tag (such as Beta), there must be a space.

 - A change of z means that this is an optional update and is compatible with both previous and next versions;
 - A change of y means that this is a important update and needs to be updated; 
 - A change of x means that this is a disruptive update and it is not recommended to use the updater but to re-download directly (but users can still request a forced update attempt)

Normally, only switching to newer versions is allowed. However, clients can use the Force Update checkbox to enable updating to any offered version.

The recommand parameter specifies the currently preferred version, which will be provided as the default if available.

#### package.toml

This is the configuration file that specifically manages each version

~~~ toml
[common]
author = "Damedane"
version = "1.0.0"
program = "1.0.0" (optional)
remote = "https://raw.githubusercontent.com/"

[files]
file1 = { path = "a.txt", dir = "a/a.txt", action = "delete", version = 1 }
file2 = { path = "a/b.txt", version = 1 }
file3 = { path = "c.txt", version = 2 }

[extra]
command = "c.txt"
~~~
For example, this file said that created by `Damedane`, and indicates that the 1.0.0 updater is needed to complete the update.

The update includes: deleting a.txt, downloading b.txt to folder a, and updating c.txt (if the previous version is marked as version 2)

At the end, c.txt will be opened. Of course, you can also replace it with any bat or exe

 - dir is an optional parameter used to indicate that the local path is different from the server. Otherwise, path will be used as the actual local path.
 - action is an optional parameter used to specify other actions (such as deletion). The default value is download.
 - version is a required parameter, which represents which version of this file this is. If the version is larger than the previous one, the file will be updated, otherwise it will be ignored.
 - The default path is the same as the updater path, but the keywords !document_dir!, !desktop_dir! and !download_dir! can be used to access the current user's Documents, Desktop and Downloads folders
 - The command in extra is also an optional parameter, which is used to open the file here after completion.
