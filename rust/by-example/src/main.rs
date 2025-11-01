#![allow(dead_code)]
#![allow(unused_imports)]

mod scheduling;
mod self_study;

use rust_by_example;

fn main() {
    // NOTE learning "by example" resources from official Rust project docs
    // - https://doc.rust-lang.org/rust-by-example
    // - https://doc.rust-lang.org/stable/book/
    // - https://doc.rust-lang.org/reference/introduction.html
    // rust_by_example::run_sections();

    // NOTE self study and templating code
    // self_study::hex_indices();
    scheduling::run();
}
