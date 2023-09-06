frappe.listview_settings['Gate Pass'] = {
    add_fields:["status"],
    get_indicator: function (doc) {
        if (doc.status === "Completed") {
            return [__("Completed"), "green", "status,=,Completed"];
        }else if(doc.status === "To Be Return"){
            return[__("To Be Return"), "orange","status,=,To Be Return"];
        }else if(doc.status === "Partially Return"){
            return[__("Partially Return"), "orange","status,=,Partially Return"];
        }
    }

}