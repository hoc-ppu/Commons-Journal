# Make papers index
Create the papers index for the House of Commons Journal. A python script can output XML (that can be typeset in InDesign) either from an existing input raw XML file or via querying the [papers laid API](http://services.paperslaid.parliament.uk/).


## Before you start
You will need to have [Python](https://www.python.org/downloads/) installed and working on your computer and, if you want to typeset the index section, a working recent version of [Adobe InDesign](https://www.adobe.com/products/indesign.html).

You should also clone this repository. [Here is a guide to cloning](https://www.youtube.com/watch?v=CKcqniGu3tA). Or if you do not have git installed you could download and extract the zip file.

## Python script installation
### *Optionally* create and activate a python virtual environment.
To create a virtual environment run the following in PowerShell on Windows or in the terminal on Unix (Mac or Linux).

<details>
<summary>On Windows</summary>

Create:
```bash
python -m venv venv
```

To activate on Windows, run:
```powershell
venv\Scripts\Activate.ps1
```

If you run into permission trouble, [this article](https://dev.to/aka_anoop/enabling-virtualenv-in-windows-powershell-ka3) may help.
</details>

<details>
<summary>On Unix</summary>

Create:
```bash
python3 -m venv venv
```

To activate on Unix, run:
```bash
source venv/bin/activate
```
</details>

### Install the dependencies (Required)
```bash
pip install -r requirements.txt
```

## Python script usage
You can either create XML from a local file or via querying the Papers Laid API.

### From API
To create XML from the Papers Laid API run the following command in your terminal or PowerShell. (replacing SESSION with a session of parliament e.g. 2016-17):
```bash
python make_papers_index.py from-api SESSION
```
Note, by default, the above will save a copy of the raw XML on your system. This is so that if you make changes to the python script (e.g. tweaking the sort order) you can use the raw file in the from file method below. You can suppress saving the raw xml with the `--discard-raw-xml` option. e.g. `python make_papers_index.py --discard-raw-xml 2015-16`

### From local file
To create output XML (for importing into InDesign) from a local (previously downloaded) raw XML API run the following command in your terminal or PowerShell. (replacing FILE with a path to file on your computer e.g.):
```bash
python make_papers_index.py from-file FILE
```

### Change where output XML files are saved
You can change the output file path of either of the above commands with `--output`. This can be a path to a file or a directory. If you enter a file path, the output XML will be saved to that path [and in the from-api version (unless you chose to discard) the raw XML from papers laid will be saved alongside the output XML but with the default file name]. If you enter a directory path, the output XML will be saved in that directory with the default file name [and in the from-api version the raw XML will be saved in that directory with the default file name].
