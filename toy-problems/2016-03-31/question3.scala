// Question 3

// Top K word count 
val K = 10
val txt: RDD[String] = sc.textFile("hdfs://big-file-with-words")
txt.flatMap(line => line.split(" ")).filter(word => word != "").map(word => (word,1)).reduceByKey(_+_).sortBy(_._2,false).take(K)
