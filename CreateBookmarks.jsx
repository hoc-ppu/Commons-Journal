//DESCRIPTION: Add Bookmarks for each dated heading in the document

// do the script but save all the steps as one step in the undo menu
// app.doScript(main, ScriptLanguage.JAVASCRIPT, undefined, UndoModes.ENTIRE_SCRIPT, "Add Bookmarks");
main();

function main(){

    var myDocument = app.activeDocument;

    // find all the date headings in the body of the journal

    foundItems = findDateHeadings(myDocument);

    alert("Found: " + foundItems.length + " date headings");

    addGroupedBookmarks(myDocument, foundItems);

    addIndexBookmarks(myDocument);

    try{
        // sort the bookmarks in the order they appear in the document
        app.menuActions.itemByID(95498).invoke();
    } catch(e){
        alert("Could not sort bookmarks");
    }

}

function addIndexBookmarks(myDocument){

    // find all the index headings in the index.
    // Also index heading1 in the business part of the index

    foundIndexHeadings = findIndexHeadings(myDocument);
    alert("Found: " + foundIndexHeadings.length + " index headings");

    for (var i = 0; i < foundIndexHeadings.length; i++) {

        foundItem = foundIndexHeadings[i];
        textContent = trim(foundItem.contents.toString());
        betterTextContenet = textContent.replace('Part ', 'Index ').replace(' – ', '. ');

        if (!myDocument.bookmarks.itemByName(betterTextContenet).isValid){
            addBookmark(myDocument, myDocument, betterTextContenet,
                        betterTextContenet, foundItem.texts[0]);
            // alert("Added: " + betterTextContenet);
        } else {
            alert("Already exists: " + betterTextContenet);
        }

        if (myDocument.bookmarks.itemByName(betterTextContenet).isValid){

            parentBookmanrk = myDocument.bookmarks.itemByName(betterTextContenet);

            foundIndexSubHeadings = findIndexSubHeadings(myDocument);

            for (var i = 0; i < foundIndexSubHeadings.length; i++) {

                foundSubItem = foundIndexSubHeadings[i];
                subTextContent = trim(foundSubItem.contents.toString());
                if (subTextContent.lastIndexOf(':') == subTextContent.length - 1){
                    subTextContent = subTextContent.substring(0, subTextContent.length - 1);
                }

                addBookmark(myDocument, parentBookmanrk, subTextContent,
                            subTextContent, foundSubItem.texts[0]);

            }
        } else {
            alert("Parent bookmark not found");
        }

    }
}

function addBookmark(myDocument, parent, destinationName, bookmarkName, location){

    // parent can be document or an existing bookmark

    if (myDocument.hyperlinkTextDestinations.itemByName(destinationName).isValid){
        // cant have destinations with the same name
        myDocument.hyperlinkTextDestinations.itemByName(destinationName).remove();
    }

    // destination
    var bookMarkDestination = myDocument.hyperlinkTextDestinations.add(location, {name:bookmarkName});

    var myBk = parent.bookmarks.add(bookMarkDestination, {name:bookmarkName});

    return myBk;
}

function addUngroupedBookmarks(myDocument, foundItems){

    for(f=0; f<foundItems.length; f++){
    // for(f=0; f<3; f++){
        foundItem = foundItems[f];

        var extracted = extractDateInfo(foundItem);

        addBookmark(
            myDocument, myDocument, extracted.date,
            extracted.date, foundItem.texts[0]
        );

    }

}

function addGroupedBookmarks(myDocument, foundItems){

    for(f=0; f<foundItems.length; f++){
    // for(f=0; f<3; f++){
        foundItem = foundItems[f];

        var extracted = extractDateInfo(foundItem);

        try{
            // optianlly group by month + year. Not sure if this will work
            // with document split over multiple files
            var monthYearBk;
            if (!myDocument.bookmarks.itemByName(extracted.monthYear).isValid){

                monthYearBk = addBookmark(
                    myDocument, myDocument, extracted.monthYear,
                    extracted.monthYear, foundItem.texts[0]
                );

            } else {
                monthYearBk = myDocument.bookmarks.itemByName(extracted.monthYear);
            }

            var myBk = addBookmark(
                myDocument, monthYearBk, extracted.date,
                extracted.date, foundItem.texts[0]
            );
        } catch(e){
            alert("Error with bookmark: " + extracted.date + "\n" + e);
        }
    }
}


function extractDateInfo(foundItem){

    // get the date without the weekday
    var date = foundItem.contents.toString().replace(/(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday) /, '');
    var month = date.match(/(January|February|March|April|May|June|July|August|September|October|November|December)/g);
    var year = date.match(/\d{4}/g);
    var monthYear = month + ' ' + year;

    return {date: date, month: month, year: year, monthYear: monthYear}
}


function findDateHeadings(myDocument){
    app.findGrepPreferences = app.changeGrepPreferences = NothingEnum.nothing;
    app.findGrepPreferences.appliedParagraphStyle = myDocument.paragraphStyleGroups.itemByName('Journal').paragraphStyles.itemByName('VotesDate');

    var myFind = myDocument.findGrep(true);  // Need to do it reveresed

    resetFindChangeGrep();

    return myFind;
}

function findIndexHeadings(myDocument){
    indexPartTitleStyle = myDocument.paragraphStyleGroups.itemByName('Journal Index').paragraphStyles.itemByName('Index_part_title');

    if (!indexPartTitleStyle.isValid){
        // alert("Index_part_title style not found");
        return [];
    }

    app.findGrepPreferences = app.changeGrepPreferences = NothingEnum.nothing;
    app.findGrepPreferences.appliedParagraphStyle = indexPartTitleStyle;

    var myFind = myDocument.findGrep(true);  // Need to do it reveresed

    resetFindChangeGrep();

    return myFind;
}

function findIndexSubHeadings(myDocument){
    app.findGrepPreferences = app.changeGrepPreferences = NothingEnum.nothing;
    app.findGrepPreferences.appliedParagraphStyle = myDocument.paragraphStyleGroups.itemByName('Journal Index').paragraphStyles.itemByName('Heading1');

    var myFind = myDocument.findGrep(true);  // Need to do it reveresed

    resetFindChangeGrep();

    return myFind;
}


function resetFindChangeGrep(){
    //Clear the find/change text preferences.
    app.findGrepPreferences = NothingEnum.nothing;
    app.changeGrepPreferences = NothingEnum.nothing;

    //Set the grep options.
    app.findChangeGrepOptions.includeFootnotes            = false;
    app.findChangeGrepOptions.includeHiddenLayers         = false;
    app.findChangeGrepOptions.includeLockedLayersForFind  = false;
    app.findChangeGrepOptions.includeLockedStoriesForFind = false;
    app.findChangeGrepOptions.includeMasterPages          = false;
}

function trim (str) {

    return str.replace(/^\s+/,'').replace(/\s+$/,'');

}
