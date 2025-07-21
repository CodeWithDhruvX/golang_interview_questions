package main

import (
	"fmt"
	"reflect"
)

type Config struct {
	Host string `env:"APP_HOST"`
	Port int    `env:"APP_PORT"`
}

func main() {
	cfg := Config{Host: "localhost", Port: 8080}
	t := reflect.TypeOf(cfg)

	for i := 0; i < t.NumField(); i++ {
		field := t.Field(i)
		fmt.Printf("Field: %s, Tag: %s\n", field.Name, field.Tag.Get("env"))
	}
}
