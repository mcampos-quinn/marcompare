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
