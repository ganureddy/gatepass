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
		if(frm.doc.docstatus === 2 && frm.doc.status !== 'Cancelled'){
			frm.add_custom_button(__('Material Returns'), function() {
				let data = [];
				
				const dialogs = new frappe.ui.Dialog({
					title: __('Item Details'),
					fields: [
						{fieldtype:'Section Break', label: __('Items')},
						{
							fieldname: "alternative_items", fieldtype: "Table", cannot_add_rows: true,
							in_place_edit: true, data: data,
							get_data: () => {
								return data;
							},
							fields: [{
								fieldtype:'Data',
								fieldname:"docname",
								hidden: 1
							},
							{
								fieldtype:'Link',
								fieldname:"item_code",
								options: 'Item',
								in_list_view: 1,
								read_only: 1,
								label: __('Item Code')
							},{
								fieldtype:'Data',
								fieldname:"item_name",
								default: "",
								fetch_from: "item_code.item_name",
								in_list_view: 1,
								label: __('Item Name'),
							},{
								fieldtype:'Float',
								fieldname:"qty",
								read_only: 1,
								in_list_view: 1,
								label: __('Qty')
							},
							{
								fieldtype:'Float',
								fieldname:"amount",
								read_only: 1,
								in_list_view: 1,
								label: __('Amount')
							},
							{
								fieldtype:'Link',
								fieldname:"uom",
								options: 'UOM',
								read_only: 1,
								in_list_view: 1,
								label: __('UOM')
							}

							]
							
						},
						
					],
					primary_action(values) {
						console.log(values,"llllllllllllllllllllllll");
					// 	frappe.call({method: "gatepass.gatepass.doctype.gate_pass.gate_pass.material_returns_through_gatepass",
					// 	args: {
					// 		name:frm.doc.name,
					// 		doctype:frm.doc.doctype,
					// 		return_item :values
					// 	},
					// });
					dialogs.hide();
				},
					size: 'medium', 
					primary_action_label: 'Return',
					
				});
				
				// To get child date and set into table
				let item = frm.doc.item
				item.forEach(child_data => {
					dialogs.fields_dict.alternative_items.df.data.push({
						"docname": child_data.name,
						"item_code": child_data.item_code,
						"item_name":child_data.item_name,
						"qty": child_data.qty,
						"uom":child_data.uom,
						"amount":child_data.amount

					});
				})
				data = dialogs.fields_dict.alternative_items.df.data;
				dialogs.fields_dict.alternative_items.grid.refresh();
				dialogs.show();
				
			})
		}
	}  
});
