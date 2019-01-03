// This is for Django's CSRF protection; see https://docs.djangoproject.com/en/1.5/ref/contrib/csrf/
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function sameOrigin(url) {
    // test that a given url is a same-origin URL
    // url could be relative or scheme relative or absolute
    var host = document.location.host; // host + port
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    // Allow absolute or scheme relative URLs to same origin
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
}
$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            // Send the token to same-origin, relative URLs only.
            // Send the token only if the method warrants CSRF protection
            // Using the CSRFToken value acquired earlier
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
// 여기서 부터 Main
$(document).ready(function () {
   
    //문서 테이블 세팅
    $('#data-table').DataTable({
        dom: '<"wrapper"frtip>',
        //"ordering": false,
        //bSort : false,
        "order": [[ 0, "desc" ]],
        language: {
            "search": '<i class="fa fa-search" aria-hidden="true"></i>',
            "searchPlaceholder": "Search"
        },
        columnDefs: [
            {
                orderable: false, "targets": '_all'
            },{
                targets: -1,
                className: 'dt-right',
            }
        ]
    });
    //Upload key file to the doc obj('ver2')
    $(".key-icon").click(function(en){
        //append hidden file upload input
        var obj = $(this);
        var fupload = $("<input type='file' style='display: none'>");
        $(this).after(fupload);
        fupload.click().change(function(e){
            var csrftoken = $("[name=csrfmiddlewaretoken]").val();
            var form_data = new FormData();
            var pk = obj.parents('tr').attr('id');

            form_data.append('file', e.target.files[0]);
            form_data.append('pk', pk)
            form_data.append('csrfmiddlewaretoken', csrftoken);
            
            var loader = $("<div class='loader' style='margin: 0 auto'></div>") 
            obj.hide();
            obj.after(loader);

            $.ajax({
                url: $('.document').attr('url'),
                type: 'POST',
                data: form_data,
                success: function (data) {
                    
                    loader.hide()
                    if (data.success == true) {
                        let keyurl = $('.document').attr('mediaurl')+data.keyurl;
                        let dom =  "<a href='"+keyurl+"' target='_blank' style='text-decoration: none'><i class='fas fa-download'></i></a> </td>";
                        obj.after(dom)
                        console.log("File upload succeeded");
                    } else {
                        obj.show();
                        console.error("error has occured");
                    }
                },
                cache: false,
                contentType: false,
                processData: false
            });
            return false;
        })
    });

    //delete the document object
    $(".delete-doc").click(function () {
        title = $(this).parents('tr').find('.doc-title').text();
        var val = confirm("Are you sure to delete\n\"" + title + "\"?")
        if (val == true) {
            var pk = $(this).parents('tr').attr('id');
            var dom = $(this).parents('tr');
            $.ajax({
                type: "GET",
                url: $('.document').attr('url'),
                data: {
                    'pk': pk,
                    'action': 'delete'
                },
                success: function (response) {
                    if (response.success == true) {
                        dom.remove();
                    } else {
                        alert("Could not delete the object")
                    }
                },
            })
        }
    })

    //reputation increasment
    $(".reputation").contextmenu(function(e){e.preventDefault();});
    $('.reputation').mousedown(function(event) {
        var num = event.which == 1? 1 : -1;
        var obj = $(this);
        var pk = $(this).parents('tr').attr('id');

        $.ajax({
            type: "GET",
            url: $('.document').attr('url'),
            data: {
                'pk': pk,
                'action': 'reputation',
                'value': num
            },
            success: function (response) {
                if (response.success == true) {
                    console.info('reputation successfully increased to '+response.reputation)
                    obj.text(response.reputation)
                } else {
                    alert("Could not give a reputation")
                }
            },
        })
    })   
});