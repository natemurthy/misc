package main

// FieldType represents the type of a field.
type FieldType int

const (
	// Integer indicates the field's type is integer.
	Integer FieldType = iota

	// Float indicates the field's type is float.
	Float

	// Boolean indicates the field's type is boolean.
	Boolean

	// String indicates the field's type is string.
	String

	// Empty is used to indicate that there is no field.
	Empty

	// Unsigned indicates the field's type is an unsigned integer.
	Unsigned
)

func (t FieldType) String() string {
	switch t {
	case Integer:
		return "Integer"
	case Float:
		return "Float"
	case Boolean:
		return "Boolean"
	case String:
		return "String"
	case Empty:
		return "Empty"
	default:
		return "<unknown>"
	}
}
