$(function() {

    // Compare substrings when length has focus
    $('input[name=length]').focus(function() {
        $('input[name=algorithm][value=substrings]').prop('checked', true);
    });

});
