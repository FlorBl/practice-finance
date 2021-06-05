document.addEventListener('DOMContentLoaded', function(){
var apiKey = "pk_8a2179db5a5c4bd4a1c8e6e2d6e51cc8";
 // variable 
var inputt = document.getElementById("symbolone");

document.addEventListener('keyup', function (){
        var stock = document.getElementById('symbolone').value;
        var ourRequest = new XMLHttpRequest();
        ourRequest.open('GET', 'https://cloud.iexapis.com/stable/stock/'+ stock +'/quote?token='+ apiKey +'');
        
        ourRequest.onload = function() {
            if (ourRequest.status >= 200 && ourRequest.status < 400) {
                var ourData = JSON.parse(ourRequest.responseText)
                
                renderHTML(ourData);
            }
            else 
            {
                console.log("We connected to the server but it returned an error.")
            }
        };


        // Now the final step is to send our request.
        ourRequest.send();
});

// Function: gets the Company Name when the user input's the symbol
function renderHTML(ourData){
    var htmlString = [];
    var stock;
    stock = "<li><a href='#' name='stock' onclick='myFunction(this.id)' id='"+ourData['symbol']+"'>" + ourData['companyName'] + "</a></li>"
    htmlString.push(stock);

    // Copy all the value into another array and keep only unique items!

// If user presses the backspace button, remove the last child.
    inputt.addEventListener('keydown', function(event) {
        const key = event.key; 
        if (key === "Backspace" || key === "Delete") {
            stockinfo.removeChild(stockinfo.lastChild);
        }
    });

// If there's no text inside the input, empty the list.
    addEventListener('keyup', function(){
        if (inputt.value.length == 0)
        {
           // stockinfo.innerHTML = "";
            $(stockinfo).empty();
        }
        
    });
    stockinfo.insertAdjacentHTML('beforeend', htmlString);
    console.log(uniqueArray);

}

});


// Get more information by click the stock.
function myFunction(clicked_id){
var form = document.getElementById('form');
var symbol = document.getElementById('symbolone');
        symbol.value = clicked_id;
        form.submit();
}

// Buy stock 
function buystock(clicked_id){
    var form = document.getElementById('buystock');
    var symbol = document.getElementById('stocksymbol');
            symbol.value = clicked_id;
            form.submit();
            
    } 

    

// Index.html, Sell button

function micronFunction(){
    micron.getEle("#wrongUser").interaction("shake").duration(".35").timing("ease-out");
 }
function micronForm(){
    micron.getEle("#micron").interaction("flicker").duration(".35").timing("ease-out");
}
function micronSubmit(){
    micron.getEle("#micron").interaction("bounce").duration(".35").timing("ease-out");
}

// Hide Arrow on scroll
document.addEventListener('scroll', function(){
    if ($(this).scrollTop()>0)
     {
        $('#arrow').fadeOut();
     }
    else
     {
      $('#arrow').fadeIn();
     }
})


// AOS function

AOS.init({
    duration: 1200,
  })

