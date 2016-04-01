// Question 3

// Top K word count 
 val txt: RDD[String] = sc.textFile("hdfs://big-file-with-words")
 txt.flatMap(line => line.split(" ")).map(word => (word,1)).reduceByKey(_+_).sortBy().take(10)
