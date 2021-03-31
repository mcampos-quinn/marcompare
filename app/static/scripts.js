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

$(document).ready(function () {
  $('#compareTable').DataTable();
  $('.dataTables_length').addClass('bs-select');
});
