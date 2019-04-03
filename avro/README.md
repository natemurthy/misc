# avro

Some tips for working with Avro schema files. For one, use Avro IDL format instead of the JSON
schema format -- it's more human readable and less error prone, and you can just convert it
directly to the JSON schema (`*.avsc`) format. In the example here, run

```
java -jar ~/Tools/avro-tools-1.8.2.jar idl2schemata example.avdl
```

to produce `example.avsc`.

References:
* https://better-coding.com/conversion-from-apache-avro-idl-files-to-avro-schama-and-avro-protocol-files/
* https://avro.apache.org/docs/1.8.2/idl.html
