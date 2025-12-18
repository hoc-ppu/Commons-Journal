# House of Commons Journal

This projects contains two projects. `create_journal` and `make_papers_index`.

## create_journal
This python script can create a full House of Commons Journal in XML format (that can be typeset in InDesign) from a set of input raw XML files representing each day's Votes and Proceedings. Alternatively it can do this by querying the VnP API.

## make_papers_index
Create the papers index for the House of Commons Journal. A python script can output XML (that can be typeset in InDesign) either from an existing input raw XML file or via querying the [papers laid API](http://services.paperslaid.parliament.uk/).


## Before you start
You will need to have [Python](https://www.python.org/downloads/) installed and working on your computer and, if you want to typeset the index section, a working recent version of [Adobe InDesign](https://www.adobe.com/products/indesign.html).

You should also clone this repository. [Here is a guide to cloning](https://www.youtube.com/watch?v=CKcqniGu3tA). Or if you do not have git installed you could download and extract the zip file.

## Python script installation

This projects uses [uv](https://docs.astral.sh/uv/). Once you have cloned the repo and ensured that you have python and uv installed, you can install the dependencies as follows.
1. Open PowerShell on Windows or the terminal on Unix (Mac or Linux).
2. Change directory to the folder where you cloned this repository. e.g.
```bash
cd path\to\Commons-Journal
```
3. The run `uv install` to install the dependencies.
```bash
uv install
```

### *Optionally* activate the python virtual environment created by uv.
To create a virtual environment run the following in PowerShell on Windows or in the terminal on Unix (Mac or Linux).

<details>
<summary>On Windows</summary>

Run the folowing command in PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

If you run into permission trouble, [this article](https://dev.to/aka_anoop/enabling-virtualenv-in-windows-powershell-ka3) may help.
</details>

<details>
<summary>On Unix</summary>

Run the following command:
```bash
source .venv/bin/activate
```
</details>


## Python script usage

### create_journal
You can either create XML from a set of local files or via querying the VnP API.
#### From API
To create XML from the VnP API run the following command in your terminal or PowerShell. (replacing SESSION with a session of parliament e.g. 2016-17):
```bash
create_journal from-api SESSION
```
#### From local files
To create output XML (for importing into InDesign) from a set of local (previously downloaded) raw XML API files run the following command in your terminal or PowerShell. (replacing FOLDER with a path to folder on your computer e.g.):
```bash
create_journal from-folder FOLDER
```


### make_papers_index
You can either create XML from a local file or via querying the Papers Laid API.

#### From API
To create XML from the Papers Laid API run the following command in your terminal or PowerShell. (replacing SESSION with a session of parliament e.g. 2016-17):
```bash
make_papers_index from-api SESSION
```
Note, by default, the above will save a copy of the raw XML on your system. This is so that if you make changes to the python script (e.g. tweaking the sort order) you can use the raw file in the from file method below. You can suppress saving the raw xml with the `--discard-raw-xml` option. e.g. `make_papers_index --discard-raw-xml 2015-16`

#### From local file
To create output XML (for importing into InDesign) from a local (previously downloaded) raw XML API run the following command in your terminal or PowerShell. (replacing FILE with a path to file on your computer e.g.):
```bash
make_papers_index from-file FILE
```

#### Change where output XML files are saved
You can change the output file path of either of the above commands with `--output`. This can be a path to a file or a directory. If you enter a file path, the output XML will be saved to that path [and in the from-api version (unless you chose to discard) the raw XML from papers laid will be saved alongside the output XML but with the default file name]. If you enter a directory path, the output XML will be saved in that directory with the default file name [and in the from-api version the raw XML will be saved in that directory with the default file name].
