// $("#equivalentRecords").hide();
$('.equivalentRecords').show();
$('.diffRecords').show();
$(".btn").click(function () {
	var id = $(this).attr("id");
  if(id == "show-discrepancies"){
	  $(this);
  	$('.equivalentRecords').hide();
  }else{
	  $(this);
		$('.equivalentRecords').show();
  }
});


// Bootstrap-table function for export... doesn't really do what i want....
// https://examples.bootstrap-table.com/#extensions/export.html#view-source
//
var $table = $('#table')
$(function() {
  $('#toolbar').find('select').change(function () {
    $table.bootstrapTable('destroy').bootstrapTable({
      exportDataType: $(this).val(),
      exportTypes: ['json','csv', 'txt','excel'],
      columns: [
        {
          field: 'state',
          checkbox: true,
          visible: $(this).val() === 'selected'
        },
        {
          field: 'row',
          title: 'Row'
        }, {
          field: 'record1',
          title: 'record 1'
        }, {
          field: 'record2',
          title: 'record2'
        }
      ]
    })
  }).trigger('change')
})
// this is for displaying tables using JQuery DataTables
// var table = $('#compareTable').DataTable();
//
// var filteredRows = function selectOnlyFiltered(){
//     table.rows({filter: 'applied'});
// }
// $(document).ready(function () {
// 	// $('#compareTable').DataTable();
// 	selectOnlyFiltered();
//   $('.dataTables_length').addClass('bs-select');
// });
