#![allow(dead_code)]


// Section 1 : https://doc.rust-lang.org/rust-by-example/hello.html
fn section_01() {
    formatted_print();
    print_debug();
    print_display();
    print_display_list();
    print_formatting();
}


// Section 1.2
// Code pasted from https://doc.rust-lang.org/rust-by-example/hello/print.html
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

    // disable `dead_code` which warn against unused module
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
        age: u8 // smallest primitive data type in Rust
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
}


// Section 1.2.2.1
// https://doc.rust-lang.org/rust-by-example/hello/print/print_display/testcase_list.html
fn print_display_list() {
    use std::fmt;

    struct List(Vec<i32>);

    impl fmt::Display for List {
        fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
            // Extract the value using tuple indexing,
            // and create a reference to `vec`.
            let vec = &self.0;

            // Introduces the ? operator for chaining write!()s
            write!(f, "[")?;

            // Iterate over `v` in `vec` while enumerating the iteration
            // index in `index`.
            for (index, v) in vec.iter().enumerate() {
                // For every element except the first, add a comma.
                // Use the ? operator to return on errors.
                if index != 0 { write!(f, ", ")?; }
                write!(f, "{}", v)?;
            }

            // Close the opened bracket and return a fmt::Result value.
            write!(f, "]")
        }
    }

    let v = List(vec![1, 2, 3]);
    println!("{}", v);
}


// Section 1.2.3
// https://doc.rust-lang.org/rust-by-example/hello/print/fmt.html
fn print_formatting() {
    use std::fmt::{self, Formatter, Display};

    struct City {
        name: &'static str,
        // Latitude
        lat: f32,
        // Longitude
        lon: f32,
    }

    impl Display for City {
        // `f` is a buffer, and this method must write the formatted string into it.
        fn fmt(&self, f: &mut Formatter) -> fmt::Result {
            let lat_c = if self.lat >= 0.0 { 'N' } else { 'S' };
            let lon_c = if self.lon >= 0.0 { 'E' } else { 'W' };

            // `write!` is like `format!`, but it will write the formatted string
            // into a buffer (the first argument).
            write!(f, "{}: {:.3}°{} {:.3}°{}",
                   self.name, self.lat.abs(), lat_c, self.lon.abs(), lon_c)
        }
    }

    #[derive(Debug)]
    struct Color {
        red: u8,
        green: u8,
        blue: u8,
    }

    for city in [
        City { name: "Dublin", lat: 53.347778, lon: -6.259722 },
        City { name: "Oslo", lat: 59.95, lon: 10.75 },
        City { name: "Vancouver", lat: 49.25, lon: -123.1 },
    ] {
        println!("{}", city);
    }
    for color in [
        Color { red: 128, green: 255, blue: 90 },
        Color { red: 0, green: 3, blue: 254 },
        Color { red: 0, green: 0, blue: 0 },
    ] {
        // Switch this to use {} once you've added an implementation
        // for fmt::Display.
        println!("{:?}", color);
    }
}


// Section 2 : https://doc.rust-lang.org/rust-by-example/primitives.html
fn section_02() {
    primitives();
    literals_and_operators();
    tuples();
    arrays_slices();
}


// Section 2
// https://doc.rust-lang.org/rust-by-example/primitives.html
#[allow(unused_variables, unused_assignments)]
fn primitives() {
    // Variables can be type annotated.
    let logical: bool = true;

    let a_float: f64 = 1.0;  // Regular annotation
    let an_integer   = 5i32; // Suffix annotation

    // Or a default will be used.
    let default_float   = 3.0; // `f64`
    let default_integer = 7;   // `i32`

    // A type can also be inferred from context.
    let mut inferred_type = 12; // Type i64 is inferred from another line.
    inferred_type = 4294967296i64;

    // A mutable variable's value can be changed.
    let mut mutable = 12; // Mutable `i32`
    mutable = 21;

    // Error! The type of a variable can't be changed.
    // mutable = true;
    //           ^^^^ expected integer, found `bool`

    // Variables can be overwritten with shadowing.
    let mutable = true;

    /* Compound types - Array and Tuple */

    // Array signature consists of Type T and length as [T; length].
    let my_array: [i32; 5] = [1, 2, 3, 4, 5];

    // Tuple is a collection of values of different types 
    // and is constructed using parentheses ().
    let my_tuple = (5u32, 1u8, true, -5.04f32);
}


// Section 2.1
// https://doc.rust-lang.org/rust-by-example/primitives/literals.html
fn literals_and_operators() {
    // Integer addition
    println!("1 + 2 = {}", 1u32 + 2);

    // Integer subtraction
    println!("1 - 2 = {}", 1i32 - 2);
    // TODO ^ Try changing `1i32` to `1u32` to see why the type is important

    // Scientific notation
    println!("1e4 is {}, -2.5e-3 is {}", 1e4, -2.5e-3);

    // Short-circuiting boolean logic
    println!("true AND false is {}", true && false);
    println!("true OR false is {}", true || false);
    println!("NOT true is {}", !true);

    // Bitwise operations
    println!("0011 AND 0101 is {:04b}", 0b0011u32 & 0b0101);
    println!("0011 OR 0101 is {:04b}", 0b0011u32 | 0b0101);
    println!("0011 XOR 0101 is {:04b}", 0b0011u32 ^ 0b0101);
    println!("1 << 5 is {}", 1u32 << 5);
    println!("0x80 >> 2 is 0x{:x}", 0x80u32 >> 2);

    // Use underscores to improve readability!
    println!("One million is written as {}", 1_000_000u32);
}


// Section 2.2
// https://doc.rust-lang.org/rust-by-example/primitives/tuples.html
fn tuples() {
    // Tuples can be used as function arguments and as return values.
    fn reverse(pair: (i32, bool)) -> (bool, i32) {
        // `let` can be used to bind the members of a tuple to variables.
        let (int_param, bool_param) = pair;

        (bool_param, int_param)
    }

    // The following struct is for the activity.
    #[derive(Debug)]
    struct Matrix(f32, f32, f32, f32);

    // A tuple with a bunch of different types.
    let long_tuple = (1u8, 2u16, 3u32, 4u64,
                      -1i8, -2i16, -3i32, -4i64,
                      0.1f32, 0.2f64,
                      'a', true);

    // Values can be extracted from the tuple using tuple indexing.
    println!("Long tuple first value: {}", long_tuple.0);
    println!("Long tuple second value: {}", long_tuple.1);

    // Tuples can be tuple members.
    let tuple_of_tuples = ((1u8, 2u16, 2u32), (4u64, -1i8), -2i16);

    // Tuples are printable.
    println!("tuple of tuples: {:?}", tuple_of_tuples);

    // But long Tuples (more than 12 elements) cannot be printed.
    //let too_long_tuple = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13);
    //println!("Too long tuple: {:?}", too_long_tuple);
    // TODO ^ Uncomment the above 2 lines to see the compiler error

    let pair = (1, true);
    println!("Pair is {:?}", pair);

    println!("The reversed pair is {:?}", reverse(pair));

    // To create one element tuples, the comma is required to tell them apart
    // from a literal surrounded by parentheses.
    println!("One element tuple: {:?}", (5u32,));
    println!("Just an integer: {:?}", (5u32));

    // Tuples can be destructured to create bindings.
    let tuple = (1, "hello", 4.5, true);

    let (a, b, c, d) = tuple;
    println!("{:?}, {:?}, {:?}, {:?}", a, b, c, d);

    let matrix = Matrix(1.1, 1.2, 2.1, 2.2);
    println!("{:?}", matrix);
}


// Section 2.3
// https://doc.rust-lang.org/rust-by-example/primitives/array.html
fn arrays_slices() {
    use std::mem;

    // This function borrows a slice.
    fn analyze_slice(slice: &[i32]) {
        println!("First element of the slice: {}", slice[0]);
        println!("The slice has {} elements", slice.len());
    }

    // Fixed-size array (type signature is superfluous).
    let xs: [i32; 5] = [1, 2, 3, 4, 5];

    // All elements can be initialized to the same value (no type signature).
    let ys = [0; 500];

    // Indexing starts at 0.
    println!("First element of the array: {}", xs[0]);
    println!("Second element of the array: {}", xs[1]);

    // `len` returns the count of elements in the array.
    println!("Number of elements in array: {}", xs.len());

    // Arrays are stack allocated.
    println!("Array occupies {} bytes", mem::size_of_val(&xs));

    // Arrays can be automatically borrowed as slices.
    println!("Borrow the whole array as a slice.");
    analyze_slice(&xs);

    // Slices can point to a section of an array.
    // They are of the form [starting_index..ending_index].
    // `starting_index` is the first position in the slice.
    // `ending_index` is one more than the last position in the slice.
    println!("Borrow a section of the array as a slice.");
    analyze_slice(&ys[1 .. 4]);

    // Example of empty slice `&[]`:
    let empty_array: [u32; 0] = [];
    assert_eq!(&empty_array, &[]);
    assert_eq!(&empty_array, &[][..]); // Same but more verbose

    // Arrays can be safely accessed using `.get`, which returns an
    // `Option`. This can be matched as shown below, or used with
    // `.expect()` if you would like the program to exit with a nice
    // message instead of happily continue.
    for i in 0..xs.len() + 1 { // Oops, one element too far!
        match xs.get(i) {
            Some(xval) => println!("{}: {}", i, xval),
            None => println!("Slow down! {} is too far!", i),
        }
    }

    // Out of bound indexing on array with constant value causes compile time error.
    //println!("{}", xs[5]);
    // Out of bound indexing on slice causes runtime error.
    //println!("{}", xs[..][5]);
}


// Section 3 : https://doc.rust-lang.org/rust-by-example/custom_types.html
fn section_03() {
    structures();
    enums();
    enums_use();
    enums_c_like();
    enums_linked_list();
    constants();
}


// Section 3.1 
// https://doc.rust-lang.org/rust-by-example/custom_types/structs.html
fn structures() {
    #[derive(Debug)]
    struct Person {
        name: String,
        age: u8,
    }

    // A unit struct
    struct Unit;

    // A tuple struct
    struct Pair(i32, f32);

    // A struct with two fields
    struct Point {
        x: f32,
        y: f32,
    }

    // Structs can be reused as fields of another struct
    struct Rectangle {
        // A rectangle can be specified by where the top left and bottom right
        // corners are in space.
        top_left: Point,
        bottom_right: Point,
    }

    // Create struct with field init shorthand
    let name = String::from("Peter");
    let age = 27;
    let peter = Person { name, age };

    // Print debug struct
    println!("{:?}", peter); // compare with dbg!(&peter);

    // Instantiate a `Point`
    let point: Point = Point { x: 5.2, y: 0.4 };
    let another_point: Point = Point { x: 10.3, y: 0.2 };

    // Access the fields of the point
    println!("point coordinates: ({}, {})", point.x, point.y);

    // Make a new point by using struct update syntax to use the fields of our other one
    let bottom_right = Point { ..another_point };

    // `bottom_right.y` will be the same as `another_point.y` because we used that field
    // from `another_point`
    println!("second point: ({}, {})", bottom_right.x, bottom_right.y);

    // Destructure the point using a `let` binding
    let Point { x: left_edge, y: top_edge } = point;

    let _rectangle = Rectangle {
        // struct instantiation is an expression too
        top_left: Point { x: left_edge, y: top_edge },
        bottom_right: bottom_right,
    };

    // Instantiate a unit struct
    let _unit = Unit;

    // Instantiate a tuple struct
    let pair = Pair(1, 0.1);

    // Access the fields of a tuple struct
    println!("pair contains {:?} and {:?}", pair.0, pair.1);

    // Destructure a tuple struct
    let Pair(integer, decimal) = pair;

    println!("pair contains {:?} and {:?}", integer, decimal);
}


// Section 3.2
// https://doc.rust-lang.org/rust-by-example/custom_types/enum.html
fn enums() {
    // Create an `enum` to classify a web event. Note how both
    // names and type information together specify the variant:
    // `PageLoad != PageUnload` and `KeyPress(char) != Paste(String)`.
    // Each is different and independent.
    enum WebEvent {
        // An `enum` variant may either be `unit-like`,
        PageLoad,
        PageUnload,
        // like tuple structs,
        KeyPress(char),
        Paste(String),
        // or c-like structures.
        Click { x: i64, y: i64 },
    }

    // A function which takes a `WebEvent` enum as an argument and
    // returns nothing.
    fn inspect(event: WebEvent) {
        match event {
            WebEvent::PageLoad => println!("page loaded"),
            WebEvent::PageUnload => println!("page unloaded"),
            // Destructure `c` from inside the `enum` variant.
            WebEvent::KeyPress(c) => println!("pressed '{}'.", c),
            WebEvent::Paste(s) => println!("pasted \"{}\".", s),
            // Destructure `Click` into `x` and `y`.
            WebEvent::Click { x, y } => {
                println!("clicked at x={}, y={}.", x, y);
            },
        }
    }

    let pressed = WebEvent::KeyPress('x');
    // `to_owned()` creates an owned `String` from a string slice.
    let pasted  = WebEvent::Paste("my text".to_owned());
    let click   = WebEvent::Click { x: 20, y: 80 };
    let load    = WebEvent::PageLoad;
    let unload  = WebEvent::PageUnload;

    inspect(pressed);
    inspect(pasted);
    inspect(click);
    inspect(load);
    inspect(unload);
}


// Section 3.2.1
// https://doc.rust-lang.org/rust-by-example/custom_types/enum/enum_use.html
fn enums_use() {
    // An attribute to hide warnings for unused code.
    enum Stage {
        Beginner,
        Advanced,
    }

    enum Role {
        Student,
        Teacher,
    }
    
    // Explicitly `use` each name so they are available without manual scoping.
    // Would need `use crate::Stage` if `enum Stage` is defined outside the scope of
    // the `fn enum_use()`.
    use Stage::{Beginner, Advanced};
    // Automatically `use` each name inside `Role`.
    use Role::*;

    // Equivalent to `Stage::Beginner`.
    let stage = Beginner;
    // Equivalent to `Role::Student`.
    let role = Student;

    match stage {
        // Note the lack of scoping because of the explicit `use` above.
        Beginner => println!("Beginners are starting their learning journey!"),
        Advanced => println!("Advanced learners are mastering their subjects..."),
    }

    match role {
        // Note again the lack of scoping.
        Student => println!("Students are acquiring knowledge!"),
        Teacher => println!("Teachers are spreading knowledge!"),
    }
}


// Section 3.2.2
// https://doc.rust-lang.org/rust-by-example/custom_types/enum/c_like.html
fn enums_c_like() {
    // enum with implicit discriminator (starts at 0)
    enum Number {
        Zero,
        One,
        Two,
    }

    // enum with explicit discriminator
    enum Color {
        Red = 0xff0000,
        Green = 0x00ff00,
        Blue = 0x0000ff,
    }
    use Number::*;
    use Color::*;

    // `enums` can be cast as integers (u8, i8, u16, i32, etc).
    println!("zero is {}", Zero as u8);
    println!("one is {}", One as i8);
    println!("two is {}", Two as u16);

    // these enums need at least 24 bits (u8 * 3)
    println!("roses are #{:06x}", Red as u32);
    println!("grass is #{:06x}", Green as i32);
    println!("violets are #{:06x}", Blue as u64);
}


// Section 3.2.3
// https://doc.rust-lang.org/rust-by-example/custom_types/enum/testcase_linked_list.html
fn enums_linked_list() { 
    enum List {
        // Cons: Tuple struct that wraps an element and a pointer to the next node
        Next(u32, Box<List>),
        // Nil: A node that signifies the end of the linked list
        Nil,
    }

    // Methods can be attached to an enum
    impl List {
        // Create an empty list
        fn new() -> List {
            // `Nil` has type `List`
            Nil
        }

        // Consume a list, and return the same list with a new element at its front
        fn prepend(self, elem: u32) -> List {
            // `Cons` also has type List
            Next(elem, Box::new(self))
        }

        // Return the length of the list
        fn len(&self) -> u32 {
            // `self` has to be matched, because the behavior of this method
            // depends on the variant of `self`
            // `self` has type `&List`, and `*self` has type `List`, matching on a
            // concrete type `T` is preferred over a match on a reference `&T`
            // after Rust 2018 you can use self here and tail (with no ref) below as well,
            // rust will infer &s and ref tail. 
            // See https://doc.rust-lang.org/edition-guide/rust-2018/ownership-and-lifetimes/default-match-bindings.html
            match *self {
                // Can't take ownership of the tail, because `self` is borrowed;
                // instead take a reference to the tail
                // And it'a a non-tail recursive call which may cause stack overflow for
                // long lists.
                Next(_, ref tail) => 1 + tail.len(),
                // Base Case: An empty list has zero length
                Nil => 0
            }
        }

        // Return representation of the list as a (heap allocated) string
        fn stringify(&self) -> String {
            match *self {
                Next(head, ref tail) => {
                    // `format!` is similar to `print!`, but returns a heap
                    // allocated string instead of printing to the console
                    format!("{}, {}", head, tail.stringify())
                },
                Nil => {
                    format!("Nil")
                },
            }
        }
    }

    use List::*;

    // Create an empty linked list
    let mut list = List::new();

    // Prepend some elements
    list = list.prepend(1);
    list = list.prepend(2);
    list = list.prepend(3);

    // Show the final state of the list
    println!("linked list has length: {}", list.len());
    println!("{}", list.stringify());
}


// Section 3.3
// https://doc.rust-lang.org/rust-by-example/custom_types/constants.html
// Globals are declared outside all other scopes.
static LANGUAGE: &str = "Rust";
const THRESHOLD: i32 = 10;

fn constants() {
    fn is_big(n: i32) -> bool {
        // Access constant in some function
        n > THRESHOLD
    }

    let n = 16;

    // Access constant in the main thread
    println!("This is {}", LANGUAGE);
    println!("The threshold is {}", THRESHOLD);
    println!("{} is {}", n, if is_big(n) { "big" } else { "small" });

    // Error! Cannot modify a `const`.
    // THRESHOLD = 5;
    // FIXME ^ Comment out this line
}


// Section 4 : https://doc.rust-lang.org/rust-by-example/variable_bindings.html
fn section_04() {
    variable_bindings();
    mutability();
    scope_and_shadowing();
    declare_first();
    freeze();
}


// Section 4
fn variable_bindings() {
    let an_integer = 1u32;
    let a_boolean = true;
    let unit = ();

    // copy `an_integer` into `copied_integer`
    let copied_integer = an_integer;

    println!("An integer: {:?}", copied_integer);
    println!("A boolean: {:?}", a_boolean);
    println!("Meet the unit value: {:?}", unit);

    // The compiler warns about unused variable bindings; these warnings can
    // be silenced by prefixing the variable name with an underscore
    let _unused_variable = 3u32;

    let _noisy_unused_variable = 2u32;
    // FIXME ^ Prefix with an underscore to suppress the warning
    // Please note that warnings may not be shown in a browser
}


// Section 4.1
// https://doc.rust-lang.org/rust-by-example/variable_bindings/mut.html
fn mutability() {
    let _immutable_binding = 1;
    let mut mutable_binding = 1;

    println!("Before mutation: {}", mutable_binding);

    // Ok
    mutable_binding += 1;

    println!("After mutation: {}", mutable_binding);

    // NOTE rror! Cannot assign a new value to an immutable variable
    // _immutable_binding += 1;
}


// Section 4.2
// https://doc.rust-lang.org/rust-by-example/variable_bindings/scope.html
fn scope_and_shadowing() {
    // This binding lives in the main function
    let long_lived_binding = 1;

    // This is a block, and has a smaller scope than the main function
    {
        // This binding only exists in this block
        let short_lived_binding = 2;

        println!("inner short-lived: {}", short_lived_binding);
    }
    // End of the block

    // Error! `short_lived_binding` doesn't exist in this scope
    // println!("outer short: {}", short_lived_binding);
    // FIXME ^ Comment out this line

    println!("outer long-lived: {}", long_lived_binding);

    let shadowed_binding = 1;

    {
        println!("before being shadowed: {}", shadowed_binding);

        // This binding *shadows* the outer one
        // NOTE the type change
        let shadowed_binding = "abc";

        println!("shadowed in inner block: {}", shadowed_binding);
    }

    // NOTE the value of this vaiable remains unchanged because shadowing binding
    // from the inner block above remains scoped only to that block
    println!("outside inner block: {}", shadowed_binding);

    // This binding *shadows* the previous binding
    let shadowed_binding = 2;
    println!("shadowed in outer block: {}", shadowed_binding);
}


// Section 4.3
// https://doc.rust-lang.org/rust-by-example/variable_bindings/declare.html
fn declare_first() {
    // Declare a variable binding first (without type set)
    let a_binding;

    {
        let x = 2;

        // Initialize the binding
        a_binding = x * x;
    }

    println!("a binding: {}", a_binding);

    let another_binding;

    // Error! Use of uninitialized binding
    // println!("another binding: {}", another_binding);
    // FIXME ^ Comment out this line

    another_binding = 1;

    println!("another binding: {}", another_binding);
}


// Section 4.4
// https://doc.rust-lang.org/rust-by-example/variable_bindings/freeze.html
fn freeze() {
    let mut _mutable_integer = 7i32;

    {
        // Shadowing immutable `_mutable_integer` will "freeze" this variable within
        // this block scope
        let _mutable_integer = _mutable_integer;

        // Error! `_mutable_integer` is frozen in this scope
        // _mutable_integer = 50;
        // FIXME ^ Comment out this line

        // `_mutable_integer` goes out of scope
    }

    // Ok! `_mutable_integer` is not frozen in this scope
    _mutable_integer = 3;
}


// Section 5 : https://doc.rust-lang.org/rust-by-example/types.html
fn section_05() {
    casting();
    literals();
    inference();
    alias();
}


// Section 5.1
// https://doc.rust-lang.org/rust-by-example/types/cast.html
#[allow(overflowing_literals)]  // Suppress all warnings from casts which overflow.
fn casting() {
    let decimal = 65.4321_f32;

    // Error! No implicit conversion
    // let integer: u8 = decimal;
    // FIXME ^ Comment out this line

    // Explicit conversion
    let integer = decimal as u8;
    let character = integer as char;

    // Error! There are limitations in conversion rules.
    // A float cannot be directly converted to a char.
    // let character = decimal as char;
    // FIXME ^ Comment out this line

    println!("Casting: {} -> {} -> {}", decimal, integer, character);

    // when casting any value to an unsigned type, T,
    // T::MAX + 1 is added or subtracted until the value
    // fits into the new type

    // 1000 already fits in a u16
    println!("1000 as a u16 is: {}", 1000 as u16);

    // 1000 - 256 - 256 - 256 = 232
    // Under the hood, the first 8 least significant bits (LSB) are kept,
    // while the rest towards the most significant bit (MSB) get truncated.
    println!("1000 as a u8 is : {}", 1000 as u8);
    // -1 + 256 = 255
    println!("  -1 as a u8 is : {}", (-1i8) as u8);

    // For positive numbers, this is the same as the modulus
    println!("1000 mod 256 is : {}", 1000 % 256);

    // When casting to a signed type, the (bitwise) result is the same as
    // first casting to the corresponding unsigned type. If the most significant
    // bit of that value is 1, then the value is negative.

    // Unless it already fits, of course.
    println!(" 128 as a i16 is: {}", 128 as i16);

    // In boundary case 128 value in 8-bit two's complement representation is -128
    println!(" 128 as a i8 is : {}", 128 as i8);

    // repeating the example above
    // 1000 as u8 -> 232
    println!("1000 as a u8 is : {}", 1000 as u8);
    // and the value of 232 in 8-bit two's complement representation is -24
    println!(" 232 as a i8 is : {}", 232 as i8);

    // Since Rust 1.45, the `as` keyword performs a *saturating cast*
    // when casting from float to int. If the floating point value exceeds
    // the upper bound or is less than the lower bound, the returned value
    // will be equal to the bound crossed.

    // 300.0 as u8 is 255
    println!(" 300.0 as u8 is : {}", 300.0_f32 as u8);
    // -100.0 as u8 is 0
    println!("-100.0 as u8 is : {}", -100.0_f32 as u8);
    // nan as u8 is 0
    println!("   nan as u8 is : {}", f32::NAN as u8);

    // This behavior incurs a small runtime cost and can be avoided
    // with unsafe methods, however the results might overflow and
    // return **unsound values**. Use these methods wisely:
    unsafe {
        // 300.0 as u8 is 44
        println!(" 300.0 as u8 is : {}", 300.0_f32.to_int_unchecked::<u8>());
        // -100.0 as u8 is 156
        println!("-100.0 as u8 is : {}", (-100.0_f32).to_int_unchecked::<u8>());
        // nan as u8 is 0
        println!("   nan as u8 is : {}", f32::NAN.to_int_unchecked::<u8>());
    }
}


// Section 5.2
// https://doc.rust-lang.org/rust-by-example/types/literals.html
fn literals() {
    // Suffixed literals, their types are known at initialization
    let x = 1u8;
    let y = 2u32;
    let z = 3f32;

    // Unsuffixed literals, their types depend on how they are used
    let i = 1;
    let f = 1.0;

    // `size_of_val` returns the size of a variable in bytes
    println!("size of `x` in bytes: {}", std::mem::size_of_val(&x));
    println!("size of `y` in bytes: {}", std::mem::size_of_val(&y));
    println!("size of `z` in bytes: {}", std::mem::size_of_val(&z));
    println!("size of `i` in bytes: {}", std::mem::size_of_val(&i));
    println!("size of `f` in bytes: {}", std::mem::size_of_val(&f));
}


// Section 5.3
// https://doc.rust-lang.org/rust-by-example/types/inference.html
fn inference() {
    // Because of the annotation, the compiler knows that `elem` has type u8.
    let elem = 7_u8;

    // Create an empty vector (a growable array).
    let mut vec = Vec::new();
    // At this point the compiler doesn't know the exact type of `vec`, it
    // just knows that it's a vector of something (`Vec<_>`).

    // Insert `elem` in the vector.
    // Aha! Now the compiler knows that `vec` is a vector of `i8`s (`Vec<u8>`)
    vec.push(elem); // type inference happens here
    vec.push(2); // also enforces type check when push() is called
    vec.push(88);
    

    // TODO try commenting out the push() lines below
    // the literal `256` does not fit into `u8` whose range is `0..=255`
    // #[allow(overflowing_literals)] // recall from `casting()` above
    // vec.push(256);
    // Error: expected u8 but found i32
    // vec.push(-7)
    // Error: cannote change the numeric literal i32 to u8
    // vec.push(8i32);

    print_type(&vec); // Vec<i8> as inferred by `elem` at the top of this func
    println!("{:?}", vec);
}


// Section 5.4
// https://doc.rust-lang.org/rust-by-example/types/alias.html
fn alias () {
    // `NanoSecond`, `Inch`, and `U64` are new names for `u64`.
    type NanoSecond = u64;
    type Inch = u64;
    type U64 = u64;

    // `NanoSecond` = `Inch` = `U64` = `u64`.
    let nanoseconds: NanoSecond = 5 as u64;
    let inches: Inch = 2 as U64;

    // Note that type aliases *don't* provide any extra type safety, because
    // aliases are *not* new types
    println!("{} nanoseconds + {} inches = {} unit?",
             nanoseconds,
             inches,
             nanoseconds + inches);
}


// Section 6 : https://doc.rust-lang.org/rust-by-example/conversion.html
fn section_06() {
    from_into();
    try_from_into();
    to_from_string();
}


// Section 6.1
// https://doc.rust-lang.org/rust-by-example/conversion/from_into.html
fn from_into() {
    let my_str = "hello";
    let my_string = String::from(my_str);
    println!("My string is {}", my_string);

    use std::convert::{From, Into};

    #[derive(Debug)]
    struct Number {
        value: i32,
    }

    impl From<i32> for Number {
        fn from(item: i32) -> Self {
            Number { value: item }
        }
    }

    // `From` and `Into` are reciprocals of one another that are designed to be
    // complementary, but only one can be implemented on a struct that needs either
    // conversion. If one of `From` or `Into` is not commented out, then the compiler
    // will return "conflicting implementations" error.
    //
    // NOTE: If you have implemented the From trait for your type, Into will call
    // it when necessary. However, that the converse is not true: implementing
    // Into for your type will not automatically provide it with an implementation
    // of From

    // Error: see what happens if this is uncommented
    // impl Into<Number> for i32 {
    //     fn into(self) -> Number {
    //         Number { value: self }
    //     }
    // }

    // Error: if both `From` and `Into` are implemented
    let num = Number::from(30);
    println!("My number is {:?}", num);

    let int = 5;
    let num: Number = int.into();
    println!("My number is {:?}", num);
}


// Section 6.2
// https://doc.rust-lang.org/rust-by-example/conversion/try_from_try_into.html
fn try_from_into() {
    // Some conversations are falliable however and should be wrapped in a Result
    use std::convert::{TryFrom, TryInto};

    #[derive(Debug, PartialEq)]
    struct EvenNumber(i32);

    impl TryFrom<i32> for EvenNumber {
        type Error = ();

        fn try_from(value: i32) -> Result<Self, Self::Error> {
            if value % 2 == 0 {
                Ok(EvenNumber(value))
            } else {
                Err(())
            }
        }
    }

    // TryFrom
    assert_eq!(EvenNumber::try_from(8), Ok(EvenNumber(8)));
    assert_eq!(EvenNumber::try_from(5), Err(()));

    // TryInto
    let result: Result<EvenNumber, ()> = 8i32.try_into();
    assert_eq!(result, Ok(EvenNumber(8)));
    let result: Result<EvenNumber, ()> = 5i32.try_into();
    assert_eq!(result, Err(()));
}


// Section 6.3
// https://doc.rust-lang.org/rust-by-example/conversion/string.html
fn to_from_string() {

    // parse i32 to a string
    let parsed: i32 = "5".parse().unwrap(); // type inference
    let turbo_parsed = "10".parse::<i32>().unwrap(); // turbofish syntax, explicit type

    let sum = parsed + turbo_parsed;
    println!("Sum: {:?}", sum);

    use std::num::ParseIntError;
    use std::str::FromStr;

    // convert a struct to a string
    use std::fmt;

    // #[derive(Debug)]
    struct Circle {
        radius: i32
    }

    impl fmt::Display for Circle {
        fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
            write!(f, "Circle of radius {}", self.radius)
        }
    }

    let circle = Circle { radius: 6 };
    println!("{}", circle); // equivalent to circle.to_string()

    // allows for "3".parse().unwrap()
    impl FromStr for Circle {
        type Err = ParseIntError;
        fn from_str(s: &str) -> Result<Self, Self::Err> {
            match s.trim().parse() {
                Ok(num) => Ok(Circle{ radius: num }),
                Err(e) => Err(e),
            }
        }
    }

    let radius = "   3 ";
    let circle: Circle = radius.parse().unwrap(); // might panic if radius is not an int
    println!("{}", circle); // use `{:?}` to pretty print with Debug trait
}


// Section 7 : https://doc.rust-lang.org/rust-by-example/expression.html
#[allow(path_statements, unused_must_use)]
fn section_07() {
    // A Rust program is (mostly) made up of a series of statements:
    // statement
    // statement
    // statement

    // Most common statements are declarations and expressions
    let x = 5; // declare variable binding
    x;  // expressions;
    x + 1;
    15;

    // Blocks are expressions too, can be used for variable assignments: be careful
    // for presence of `;` on the last line of a block otherwise it will return `()`
    let x = 5u32;

    let y = {
        let x_squared = x * x;
        let x_cube = x_squared * x;

        // This expression will be assigned to `y`
        // NOTE: observe no semicolon is present at the end of this line
        x_cube + x_squared + x
    };

    let z = {
        // The semicolon suppresses this expression and `()` is assigned to `z`
        2 * x;
    };

    println!("x is {:?}", x);
    println!("y is {:?}", y);
    println!("z is {:?}", z);
}


// Section 8 : https://doc.rust-lang.org/rust-by-example/flow_control.html
fn section_08() {
    // if_else();
    // loop_example();
    // loop_nested_labels();
    // loop_return();
    // while_example();
    // for_range_iter();
    match_example();
}


// Section 8.1
// https://doc.rust-lang.org/rust-by-example/flow_control/if_else.html
fn if_else() {
    let n = 5;
    if n > 0 && n % 5 == 0 { // && is conditional "and" operator
        println!("{} is a natural number divisible by 5", n)
    }
}


// Section 8.2
// https://doc.rust-lang.org/rust-by-example/flow_control/loop.html
fn loop_example() {
    let mut count = 0u32;

    println!("Let's count until infinity!");

    // Infinite loop
    loop {
        count += 1;

        if count == 3 {
            println!("three");
            continue; // Skip the rest of this iteration
        }

        println!("{}", count);

        if count == 5 {
            println!("Jk, that's enough");
            break; // Exit this loop
        }
    }
}


// Section 8.2.1
// https://doc.rust-lang.org/rust-by-example/flow_control/loop/nested.html
#[allow(unreachable_code, unused_labels)]
fn loop_nested_labels() {
    'outer: loop {
        println!("Entered the outer loop");
        'inner: loop {
            println!("Entered the inner loop");
            // This would break only the inner loop
            // break;
            // This breaks the outer loop
            break 'outer;
        }
        println!("This point will never be reached");
    }
    println!("Exited the outer loop");
}


// Section 8.2.2
// https://doc.rust-lang.org/rust-by-example/flow_control/loop/return.html
fn loop_return() {
    let mut counter = 0;
    let result = loop {
        counter += 1;
        if counter == 10 {
            break counter * 2;
        }
    };
    assert_eq!(result, 20);
}

// Section 8.3
// https://doc.rust-lang.org/rust-by-example/flow_control/while.html
fn while_example() {
    // A counter variable
    let mut n = 1;

    // Loop while `n` is less than 101
    while n < 16 {
        if n % 15 == 0 {
            println!("fizzbuzz");
        } else if n % 3 == 0 {
            println!("fizz");
        } else if n % 5 == 0 {
            println!("buzz");
        } else {
            println!("{}", n);
        }

        // Increment counter
        n += 1;
    }
}


// Section 8.4
// https://doc.rust-lang.org/rust-by-example/flow_control/for.html
fn for_range_iter() {
    let mut last = 0;
    for n in 1..8 { // range includes 1 excludes 8 (half open interval)
        last = n;
    }
    println!("last {}", last);

    for n in 1..=8 { // range includes 1 and 8
        last = n;
    }
    println!("last {}", last);

    // `iter()` borrows each element in the collection leaving `names` unmoved
    let names = vec!["Bob", "Frank", "Ferris"];
    for name in names.iter() {
        match name {
            &"Ferris" => println!("There is a rustacean among us!"),
            // TODO ^ Try deleting the & and matching just "Ferris"
            _ => println!("Hello {}", name),
        }
    }
    println!("names: {:?}", names);

    // `into_iter()` consumes the collection, thus moving `names`
    let names = vec!["Bob", "Frank", "Ferris"];
    for name in names.into_iter() { 
        match name {
            "Ferris" => println!("There is a rustacean among us!"),
            _ => println!("Hello {}", name),
        }
    }
    // println!("names: {:?}", names); // Error if uncommented
    
    // `iter_mut()` allows for modifying collection in place
    let mut names = vec!["Bob", "Frank", "Ferris"];
    for name in names.iter_mut() {
        *name = match name {
            &mut "Ferris" => "There is a rustacean among us!",
            _ => "Hello",
        }
    }
    println!("names: {:?}", names);
}


// Section 8.5
// https://doc.rust-lang.org/rust-by-example/flow_control/match.html
fn match_example() {
    let number = 13;
    // TODO ^ Try different values for `number`

    println!("Tell me about {}", number);
    match number {
        // Match a single value
        1 => println!("One!"),
        // Match several values
        2 | 3 | 5 | 7 | 11  => println!("This is a prime"),
        // TODO ^ Try adding 13 to the list of prime values
        // Match an inclusive range
        13..=19 => println!("A teen"),
        // Handle the rest of cases
        _ => println!("Ain't special"),
        // TODO ^ Try commenting out this catch-all arm
    }

    let boolean = true;
    // Match is an expression too
    let binary = match boolean {
        // The arms of a match must cover all the possible values
        false => 0,
        true => 1,
        // TODO ^ Try commenting out one of these arms
    };

    println!("{} -> {}", boolean, binary);
}

fn self_learning() {
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
    println!("{:?}", &ss[0x8..0xc+3]);
    println!("{:?}", &ss[0x9..0xb+0xa]);
}

fn main() { 
    // run_all_sections();
    self_learning();
}

/* ********************************************************************************
 * Helper methods below
 * ********************************************************************************
**/

fn run_all_sections() {
    for i in 1..24 {
        match i {
            // 1 => section_01(),
            // 2 => section_02(),
            // 3 => section_03(),
            // 4 => section_04(),
            // 5 => section_05(),
            // 6 => section_06(),
            // 7 => section_07(),
            8 => section_08(),
            _ => (),
        }
    }
}

// helper method for inspecting types for all objects
fn print_type<T>(_: &T) {
    print!("{}: ", std::any::type_name::<T>());
}


