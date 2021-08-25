// Execute this after the site is loaded.
$(function() {
    // Find list items representing folders and
    // style them accordingly.  Also, turn them
    // into links that can expand/collapse the
    // tree leaf.
    $('li > ul').each(function(i) {
        // Find this list's parent list item.
        var parentLi = $(this).parent('li');

        // Style the list item as folder.
        parentLi.addClass('folder');

        // Temporarily remove the list from the
        // parent list item, wrap the remaining
        // text in an anchor, then reattach it.
        var subUl = $(this).remove();
        parentLi.wrapInner('<a/>').find('a').click(function() {
            // Make the anchor toggle the leaf display.
            subUl.toggle();
        });
        parentLi.append(subUl);
    });

    // Hide all lists except the outermost.
    $('ul ul').hide();
});

jQuery.fn.reverse = [].reverse;
$("input:checkbox").click(function()
{
	var isChecked = $(this).is(":checked");
	
	//down
	$(this).parent().next().find("input:checkbox").prop("checked", isChecked);

	//up
  $(this).parents("ul").prev("a").find("input:checkbox").reverse().each(function(a, b) {
  	$(b).prop("checked", function()
    {
      return $(b).parent("a").next("ul").find(":checked").length;
    });
  });
});