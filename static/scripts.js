function adminApprove(elem) {
    let skinName = elem.parentElement.children[0].innerHTML;
    let listItem = elem.parentElement;
    let ul = elem.parentElement.parentElement;

    $.getJSON("/approve", {
        name: skinName
    }, function(data) {
        // do nothing
    });

    // remove from list once approved
    ul.removeChild(listItem);
}