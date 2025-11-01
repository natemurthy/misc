pub fn hex_indices() {
    let ss: [String; 21] = [
        "one".to_string(),
        "two".to_string(),
        "three".to_string(),
        "four".to_string(),
        "five".to_string(),
        "six".to_string(),
        "seven".to_string(),
        "eight".to_string(),
        "nine".to_string(),
        "ten".to_string(),
        "eleven".to_string(),
        "twelve".to_string(),
        "thirteen".to_string(),
        "fourteen".to_string(),
        "fifteen".to_string(),
        "sixteen".to_string(),
        "foo".to_string(),
        "bar".to_string(),
        "baz".to_string(),
        "cap".to_string(),
        "xyz".to_string(),
    ];
    println!("{:?}", &ss[0x8..0xc + 3]);
    println!("{:?}", &ss[0x9..0xb + 0xa]);
}
