# Methods in Go Simplified

4. Methods in Go Simplified

Opening Hook (0:00–0:10)
“Think Go doesn’t support object-oriented programming? [pause] Well, that’s not exactly true — Go has methods, and they’re actually super simple. Let me show you.”

Concept Explanation (0:10–0:40)
“In Go, a method is just a function with a receiver. [pause] That receiver attaches the function to a specific type. Unlike traditional OOP languages with classes, Go attaches methods directly to structs or even custom types. [pause] It’s Go’s lightweight way of doing OOP.”

Code Walkthrough (0:40–1:20)
(show code on screen)
“Here we define a Rectangle struct with width and height.
Then, notice this line: func (r Rectangle) Area() int. This is a method. The receiver (r Rectangle) tells Go that the function belongs to the Rectangle type.
Inside the method, we just return r.w * r.h.
In main, we create a rectangle with dimensions 3 and 4, and call rect.Area(). [pause] That looks just like calling a method in other languages.
The result is 12, which is the area.”

Why It’s Useful (1:20–2:10)
“Why does this matter? [pause] Methods make your code more organized. Instead of having a random function like area(rect Rectangle), you can attach the function to the struct itself. [pause] This makes your code cleaner, more readable, and easier to maintain. [pause] You’ll see methods everywhere in Go, especially when working with interfaces, where types automatically implement behaviors if they have the right methods.”

Outro (2:10–2:30)
“So, what do you think of Go’s take on methods? [pause] Drop a comment with your thoughts, and if you’re new here, subscribe for more beginner-friendly Go tutorials.”