// ExtendScript to link dates in Index files to corresponding date headings in Journal files
// Prerequisites:
// Run JournalCreateBookmarks.jsx before running this script
// Have an open book with Index and Journal files
// Filenames within the book should contain "Index" and "Journal" respectively


// Log file paths
var bookFolder = app.activeBook.fullName.parent;
var logFile = File(bookFolder + "/Index_Link_Log.txt");
logFile.encoding = "UTF-8";
logFile.open("w");

var csvFile = File(bookFolder + "/Unlinked_Dates_Report.csv");
csvFile.encoding = "UTF-8";
csvFile.open("w");
// Write the header row for the CSV file
csvFile.writeln("Index File,Page Number,Date String");

// Log to both console and log file
function logMessage(msg) {
    $.writeln(msg);
    logFile.writeln(msg);
}

// Trim function
function trimString(str) {
    return str.replace(/^\s+|\s+$/g, '');
}

// Warn user that script will take a while
alert("Script starts when you hit OK. Put the kettle on, this may take a while. ☕");
logMessage("Starting the script...");

// Check book is open
if (app.books.length == 0) {
    alert("No book is open.");
    logFile.close();
    csvFile.close();
    exit();
}

var book = app.activeBook;
var bookContents = book.bookContents;

var indexFiles = [];
var journalFiles = [];

// Separate Index and Journal files
for (var i = 0; i < bookContents.length; i++) {
    var bc = bookContents[i];
    var docName = bc.fullName.name;
    if (docName.indexOf('Index') != -1) {
        indexFiles.push(bc);
    } else if (docName.indexOf('Journal') != -1) {
        journalFiles.push(bc);
    }
}

// Get document from book content
function getDocumentFromBookContent(bc) {
    var doc;
    for (var i = 0; i < app.documents.length; i++) {
        if (app.documents[i].fullName.fullName == bc.fullName.fullName) {
            doc = app.documents[i];
            return doc;
        }
    }
    doc = app.open(bc.fullName, false);
    return doc;
}

// Map date strings to text anchors
var dateToAnchorMap = {};

for (var i = 0; i < journalFiles.length; i++) {
    var bc = journalFiles[i];
    var doc = getDocumentFromBookContent(bc);

    // Get all text anchors
    var textAnchors = doc.hyperlinkTextDestinations;
    for (var j = 0; j < textAnchors.length; j++) {
        var anchor = textAnchors[j];
        var anchorName = trimString(anchor.name);
        dateToAnchorMap[anchorName] = anchor;
    }
    logMessage("Processed Journal file: " + doc.name);
}

// Debug: Log anchor names
logMessage("List of anchors in Journal files:");
for (var key in dateToAnchorMap) {
    if (dateToAnchorMap.hasOwnProperty(key)) {
        logMessage("Anchor name: '" + key + "'");
    }
}

// Normalize date strings for comparison
function normalizeDateString(dateStr) {
    return dateStr.replace(/\b0?(\d{1,2})\b/g, '$1').toLowerCase();
}

// Convert Index date strings to full month for Journal comparison
function convertDateToFullMonth(dateStr) {
    var monthAbbrs = {
        "Jan": "January",
        "Feb": "February",
        "Mar": "March",
        "Apr": "April",
        "May": "May",
        "Jun": "June",
        "Jul": "July",
        "Aug": "August",
        "Sep": "September",
        "Sept": "September",
        "Oct": "October",
        "Nov": "November",
        "Dec": "December"
    };

    var parts = trimString(dateStr).split(' ');
    if (parts.length != 3) {
        logMessage("Date conversion failed: Incorrect format for date '" + dateStr + "'");
        return null;
    }
    var day = parts[0];
    var abbrMonth = parts[1];
    var year = parts[2];

    var fullMonth = monthAbbrs[abbrMonth];
    if (!fullMonth) {
        logMessage("Date conversion failed: Unrecognized month abbreviation '" + abbrMonth + "' in date '" + dateStr + "'");
        return null;
    }

    var fullDate = day + ' ' + fullMonth + ' ' + year;
    logMessage("Converted date '" + dateStr + "' to '" + fullDate + "'");
    return fullDate;
}

// Progress bar
var progressWindow, progressBar;

function showProgressBar(maxValue, indexFileName) {
    progressWindow = new Window('palette', 'Processing Index Files - press ESC to cancel');
    var progressGroup = progressWindow.add('group');
    progressGroup.orientation = 'column';
    var indexFileText = progressGroup.add('statictext', undefined, 'Index File: ' + indexFileName);
    var progressText = progressGroup.add('statictext', undefined, 'Processing dates:');
    progressBar = progressGroup.add('progressbar', undefined, 0, maxValue);
    progressBar.preferredSize.width = 300;
    progressWindow.show();
}

function updateProgressBar(value, currentDate) {
    progressBar.value = value;
    progressWindow.children[0].children[1].text = 'Processing dates: ' + currentDate;
}

function closeProgressBar() {
    progressWindow.close();
}

// Track link/date counts
var totalLinksCreated = 0;
var totalDatesFound = 0;
var indexFileStats = [];

// Process Index files
for (var i = 0; i < indexFiles.length; i++) {
    var bc = indexFiles[i];
    var doc = getDocumentFromBookContent(bc);
    var indexFileName = doc.name;
    logMessage("Processing Index file: " + indexFileName);

    var indexLinksCreated = 0;
    var indexDatesFound = 0;

    app.findGrepPreferences = NothingEnum.nothing;
    app.changeGrepPreferences = NothingEnum.nothing;

    var grepPattern = "\\b\\d{1,2}\\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\\s\\d{4}\\b";
    app.findGrepPreferences.findWhat = grepPattern;

    var foundItems = doc.findGrep();
    indexDatesFound = foundItems.length; // Dates found in file
    totalDatesFound += foundItems.length; // Increment dates found

    // Show progress bar
    showProgressBar(foundItems.length, indexFileName);

    for (var j = 0; j < foundItems.length; j++) {
        var foundDate = trimString(foundItems[j].contents);
        logMessage("Found date in Index: '" + foundDate + "'");

        var fullDate = convertDateToFullMonth(foundDate);
        if (!fullDate) {
            updateProgressBar(j + 1, foundDate);
            continue; // Skip if date conversion failed
        }

        var normalizedFullDate = normalizeDateString(fullDate);
        var matchingAnchor = null;

        // Try to find a matching anchor
        for (var anchorName in dateToAnchorMap) {
            if (dateToAnchorMap.hasOwnProperty(anchorName)) {
                var normalizedAnchorName = normalizeDateString(anchorName);
                if (normalizedAnchorName === normalizedFullDate) {
                    matchingAnchor = dateToAnchorMap[anchorName];
                    break;
                }
            }
        }

        if (matchingAnchor) {
            logMessage("Found matching anchor in Journal: '" + matchingAnchor.name + "'");

            // Check if hyperlink already exists to avoid duplicates
            var existingHyperlink = null;
            for (var k = 0; k < doc.hyperlinks.length; k++) {
                var hyperlink = doc.hyperlinks[k];
                if (hyperlink.source.sourceText == foundItems[j]) {
                    existingHyperlink = hyperlink;
                    break;
                }
            }

            if (!existingHyperlink) {
                try {
                    // Create hyperlink
                    var source = doc.hyperlinkTextSources.add(foundItems[j]);
                    var hyperlink = doc.hyperlinks.add(source, matchingAnchor);
                    totalLinksCreated++; // Increment total
                    indexLinksCreated++; // Increment Index counter
                    logMessage("Created hyperlink for date: '" + foundDate + "'");
                } catch (error) {
                    logMessage("Error creating hyperlink for date: '" + foundDate + "'. Error: " + error);
                }
            } else {
                logMessage("Hyperlink already exists for date: '" + foundDate + "'");
            }
        } else {
            // No link? No anchor
            logMessage("No matching anchor found for date: '" + fullDate + "'");


            // Get page number where date found
            var pageNumber = "N/A";
            try {
                var parentPage = foundItems[j].parentTextFrames[0].parentPage;
                if (parentPage != null) {
                    pageNumber = parentPage.name;
                }
            } catch (e) {
                logMessage("Could not determine page number for date: '" + foundDate + "'");
            }

            // Write to the report
            csvFile.writeln('"' + indexFileName + '","' + pageNumber + '","' + foundDate + '"');
        }

        updateProgressBar(j + 1, foundDate);
    }

    closeProgressBar();

    app.findGrepPreferences = NothingEnum.nothing;
    app.changeGrepPreferences = NothingEnum.nothing;

    logMessage("Finished processing Index file: " + indexFileName);

    // Store stats for this Index file
    indexFileStats.push({
        fileName: indexFileName,
        datesFound: indexDatesFound,
        linksCreated: indexLinksCreated
    });
}

logMessage("Script completed.");

// Put together stats for final alert
var finalMessage = "Script has completed.\nTotal dates found in Index files: " + totalDatesFound + "\nTotal Index entries linked: " + totalLinksCreated + "\n\nDetails per Index file:\n";

for (var i = 0; i < indexFileStats.length; i++) {
    var stats = indexFileStats[i];
    finalMessage += "\nIndex File: " + stats.fileName + "\nDates found: " + stats.datesFound + "\nLinks created: " + stats.linksCreated + "\n";
}

alert(finalMessage);

logFile.close();
csvFile.close();
