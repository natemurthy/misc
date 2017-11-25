package main

import (
	"fmt"

	"github.com/spf13/viper"
)

func main() {
	viper.SetEnvPrefix("postgres")
	viper.BindEnv("database")
	viper.SetConfigType("yaml")
	viper.SetConfigName("appconfig") // name of config file (without extension)
	viper.AddConfigPath(".")         // optionally look for config in the working directory
	err := viper.ReadInConfig()      // Find and read the config file
	if err != nil {                  // Handle errors reading the config file
		panic(fmt.Errorf("Fatal error config file: %s \n", err))
	}
	fmt.Println(viper.Get("database.password"))
}
