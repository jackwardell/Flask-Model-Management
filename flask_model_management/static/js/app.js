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