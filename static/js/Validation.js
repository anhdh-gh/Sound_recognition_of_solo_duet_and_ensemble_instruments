jQuery.validator.addMethod("notBlank", function (value, element) {
    return value.trim().length > 0;
}, "No space please and don't leave it empty");

jQuery.validator.addMethod("phoneNumber", function (value, element) {
    return value.match(/([0-9]{10})|(\([0-9]{3}\)\s+[0-9]{3}\-[0-9]{4})/);
}, "Phone number không đúng định dạng");

