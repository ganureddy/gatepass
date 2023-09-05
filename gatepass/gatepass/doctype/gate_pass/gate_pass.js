// Copyright (c) 2023, Ganu Reddy and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gate Pass', {
	party: function(frm) {
		if(frm.doc.party != '' && frm.doc.party_type != ''){
			frappe.call({
				method:"gatepass.gatepass.doctype.gate_pass.gate_pass.party_address_details",
				args:{
					party:frm.doc.party,
					party_type:frm.doc.party_type,
					company:frm.doc.company
				},
				callback: function(r){
					if (r.message){
						frm.set_value("company_address_name",r.message.company_address)
						frm.set_value("shipping_address_name",r.message.shipping_address_name)
						let company_address_display = r.message.company_address_display.replace("<br>\n","\n")
						let company_details = company_address_display.split("<br>")
						let comp_value = ''
						for (let i = 0; i < company_details.length; i++) {
							comp_value += company_details[i] + '\n'
						};
						frm.set_value("company_address",comp_value);
						let shipping_address = r.message.shipping_address.replace("<br>\n","\n");
						let new_value = shipping_address.split("<br>");
						let custom_value = '';
						for (let j = 0; j < new_value.length; j++) {
							custom_value += new_value[j] + '\n'
						};
						frm.set_value("shipping_address",custom_value);
					}
				}
	
			})
		}
		
	}
});


frappe.ui.form.on('Gate Pass', {
    refresh: function(frm) {
        frm.add_custom_button(__('Material Returns'), function() {
            frappe.call({method: "gatepass.gatepass.doctype.gate_pass.gate_pass.material_returns",
            // args: {
            //     "mobile_no":frm.doc.mobile_no,
            // },
        })
    });
}});
