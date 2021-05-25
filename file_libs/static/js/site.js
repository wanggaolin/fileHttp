function code_image_show(dir,file) {
    $("#file_code").show();
    $("#file_code").attr("src", "/file/code?dir=" + dir + "&file=" + file + "&n=" + new Date().getTime());
}
function code_image_hide() {
    $("#file_code").hide();
}