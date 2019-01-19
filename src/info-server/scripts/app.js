const http = require("http");
const port = 3000;
var date = new Date();
let start_timestamp = date.getTime();
let alert = 1.0

const requestHandler = (request, response) => {

  if (request.url == '/alert') {
     alert = 1.01 - alert
  }

  let d = new Date();
  current_timestamp = d.getTime();
  let diff = (current_timestamp - start_timestamp) / 10000
  response.end(
    `app_melt_volt{side="0.1"} ${ (1.0 + Math.sin(diff) ) * alert }`
  );
};

const server = http.createServer(requestHandler);

server.listen(port, err => {
  if (err) {
    return console.log("something bad happened", err);
  }

  console.log(`server is listening on ${port}`);
});
