function getFormData(formId, reset) {
    var formData = $("#" + formId + " :input")
        .filter(function (index, element) {
            return $(element).val() != '';
        })
        .serialize();
    if (reset) {
        $("#" + formId).trigger("reset");
    }
    return formData
}

$(".date").flatpickr({
    wrap: true
});

$(".datetime").flatpickr({
    wrap: true,
    enableTime: true,
});
