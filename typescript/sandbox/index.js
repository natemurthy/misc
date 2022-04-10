var id = 5;
console.log(id);
var Direction1;
(function (Direction1) {
    Direction1["Up"] = "Up";
    Direction1["Down"] = "Down";
    Direction1["Left"] = "Left";
    Direction1["Right"] = "Right";
})(Direction1 || (Direction1 = {}));
console.log(Direction1.Up);
var user = {
    id: 0,
    name: 'John'
};
console.log(user);
// Type Assertion (two was of doing this)
var cid = 1;
//let customerId = <number>cid
var customerId = cid;
console.log(customerId);
function addNum(x, y) {
    return x + y;
}
var user1 = { id: 1, name: 'one' };
var user2 = { id: 2, name: 'two' };
console.log(addNum(user1.id, user2.id));
