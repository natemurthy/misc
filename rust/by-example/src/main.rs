// Section 1.2
// Code pasted from https://doc.rust-lang.org/rust-by-example/hello/print.html
#[allow(dead_code)]
fn formatted_print() {
    // In general, the `{}` will be automatically replaced with any
    // arguments. These will be stringified.
    println!("{} days", 31);

    // Positional arguments can be used. Specifying an integer inside `{}`
    // determines which additional argument will be replaced. Arguments start
    // at 0 immediately after the format string.
    println!("{0}, this is {1}. {1}, this is {0}", "Alice", "Bob");

    // As can named arguments.
    println!("{subject} {verb} {object}",
             object="the lazy dog",
             subject="the quick brown fox",
             verb="jumps over");

    // Different formatting can be invoked by specifying the format character
    // after a `:`.
    println!("Base 10:               {}",   69420); // 69420
    println!("Base 2 (binary):       {:b}", 69420); // 10000111100101100
    println!("Base 8 (octal):        {:o}", 69420); // 207454
    println!("Base 16 (hexadecimal): {:x}", 69420); // 10f2c

    // You can right-justify text with a specified width. This will
    // output "    1". (Four white spaces and a "1", for a total width of 5.)
    println!("{number:>5}", number=1);

    // You can pad numbers with extra zeroes,
    println!("{number:0>5}", number=1); // 00001
    // and left-adjust by flipping the sign. This will output "10000".
    println!("{number:0<5}", number=1); // 10000

    // You can use named arguments in the format specifier by appending a `$`.
    println!("{number:0>width$}", number=1, width=5);

    // Rust even checks to make sure the correct number of arguments are used.
    println!("My name is {0}, {1} {0}", "Bond", "James");
    // FIXED ^ Added the missing argument: "James"

    // Only types that implement fmt::Display can be formatted with `{}`. User- 
    // defined types do not implement fmt::Display by default.

    #[allow(dead_code)] // disable `dead_code` which warn against unused module
    struct Structure(i32);

    // This will not compile because `Structure` does not implement
    // fmt::Display.
    // println!("This struct `{}` won't print...", Structure(3));
    // TODO ^ Try uncommenting this line

    // For Rust 1.58 and above, you can directly capture the argument from a
    // surrounding variable. Just like the above, this will output
    // "    1", 4 white spaces and a "1".
    let number: f64 = 1.0;
    let width: usize = 5;
    println!("{number:>width$}");
}


// Section 1.2.1
// https://doc.rust-lang.org/rust-by-example/hello/print/print_debug.html
#[allow(dead_code)]
fn print_debug() {
    // This structure cannot be printed either with `fmt::Display` or
    // with `fmt::Debug`.
    struct UnPrintable(i32);

    // The `derive` attribute automatically creates the implementation
    // required to make this `struct` printable with `fmt::Debug`.
    #[derive(Debug)]
    struct DebugPrintable(i32);

    // Put a `Structure` inside of the structure `Deep`. Make it printable
    // also.
    #[derive(Debug)]
    struct Deep(DebugPrintable);

    #[derive(Debug)]
    struct Person<'a> {
        name: &'a str,
        age: u8
    }

    // Will result in rustc error E0277
    // println!("This {:?} will not print", UnPrintable(2));
    // NOTE ^ Try uncommenting this line

    // `Structure` is printable!
    println!("Now {:?} will print!", DebugPrintable(3));

    // The problem with `derive` is there is no control over how
    // the results look. What if I want this to just show a `7`?
    println!("Now {:?} will print!", Deep(DebugPrintable(7)));

    let name = "Peter";
    let age = 27;
    let peter = Person { name, age };

    // Pretty print
    println!("{:#?}", peter);

}


// Section 1.2.2
// https://doc.rust-lang.org/rust-by-example/hello/print/print_display.html
#[allow(dead_code)]
fn print_display() {
    // Import (via `use`) the `fmt` module to make it available.
    use std::fmt;

    // A structure holding two numbers. `Debug` will be derived so the results can
    // be contrasted with `Display`.
    #[derive(Debug)]
    struct MinMax(i64, i64);

    // Implement `Display` for `MinMax`.
    impl fmt::Display for MinMax {
        fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
            // Use `self.number` to refer to each positional data point.
            write!(f, "({}, {})", self.0, self.1)
        }
    }

    // Define a structure where the fields are nameable for comparison.
    #[derive(Debug)]
    struct Point2D {
        x: u8,
        y: u16,
    }

    // Similarly, implement `Display` for `Point2D`.
    impl fmt::Display for Point2D {
        fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
            // Customize so only `x` and `y` are denoted.
            write!(f, "x: {}, y: {}", self.x, self.y)
        }
    }

    impl fmt::Binary for Point2D {
        fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
            write!(f, "{:b} {:b}", self.x, self.y)
        }
    }

    let minmax = MinMax(0, 14);

    println!("Compare structures:");
    println!("Display: {}", minmax);
    println!("Debug: {:?}", minmax);

    let big_range =   MinMax(-300, 300);
    let small_range = MinMax(-3, 3);

    println!("The big range is {big} and the small is {small}",
             small = small_range,
             big = big_range);

    let point = Point2D { x: 3, y: 7 };

    println!("Compare points:");
    println!("Display: {}", point);
    println!("Debug: {:?}", point);

    // Error. Both `Debug` and `Display` were implemented, but `{:b}`
    // requires `fmt::Binary` to be implemented. This will not work.
    println!("What does Point2D look like in binary: {:b}?", point);

    // To get a byte-by-byte representation of the struct's memory, you can 
    // convert it into a byte slice (which often requires using unsafe code
    // or libraries designed for safe byte-level acces
    use std::mem;

    #[repr(C)] // Ensures C-compatible memory layout for predictable byte representation
    struct MyStruct {
        a: u8,
        b: u16,
    }

    let x = MyStruct { a: 3, b: 7 };

    // Unsafe: Directly casting a struct to a byte slice
    // Use with caution and ensure #[repr(C)] for predictable layout
    let bytes: &[u8] = unsafe {
        std::slice::from_raw_parts(
            &x as *const MyStruct as *const u8,
            mem::size_of::<MyStruct>(),
        )
    };

    print!("Struct bytes: [");
    for (i, byte) in bytes.iter().enumerate() {
        print!("{:08b}", byte); // Prints each byte in binary
        if i < bytes.len() - 1 {
            print!(", ");
        }
    }
    println!("]");
}

fn main() {
    // formatted_print();
    // print_debug();
    print_display();
}
