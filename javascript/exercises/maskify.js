/* 

1. Usually when you buy something, you're asked whether your credit card number, phone number or answer to your most secret question is still correct. However, since someone could look over your shoulder, you don't want that shown on your screen. Instead, we mask it.

Your task is to write a function maskify, which changes all but the last four characters into '#'.

This function should take all characters as a paramater, not just integers. If it's given an empty string as a paramater, your function should return an empty string back – it should NOT return undefined or null.

examples: 

maskify(123456789); // => returns #####6789
maskify(123); // => returns 123
maskify(maskify); // => returns ###kify
maskify(''); // => returns ''

*/

function solution1(w) {
        n = w.length
        if (n > 4) {
                d = n-4;
                lastFour = w.substr(d);
                mask = "#".repeat(d);
                return mask + lastFour;

        } else {
                return w;
        }
}

function solution2(w) {
        return w.replace(/\S(?=\S{4})/g, "#");
}

function solution3(w) {
        return w.replace(/.(?=....)/g, "#");
}

function maskify(str) {
        return solution1(str);
}


pswd = "sqY&%(hfs1234";
console.log(maskify(pswd));
console.log(maskify("123456789"));
console.log(maskify("123"));
console.log(maskify("maskify"));
console.log("");

