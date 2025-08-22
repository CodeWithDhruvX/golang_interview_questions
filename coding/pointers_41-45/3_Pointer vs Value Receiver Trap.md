# Pointer vs Value Receiver Trap

3. Pointer vs Value Receiver Trap

Opening Hook (0:00–0:10)
“Seventy percent of Go candidates fail this question: what’s the difference between pointer receivers and value receivers? [pause] Let’s break it down with code.”

Concept Explanation (0:10–0:40)
“In Go, methods can have either value receivers or pointer receivers. [pause] A value receiver means the method gets a copy of the object. A pointer receiver means the method can directly modify the original. [pause] If you mix these up, you’ll introduce sneaky bugs.”

Code Walkthrough (0:40–1:20)
(show code on screen)
“We have a User struct with a name field.
First method: SetNameValue uses a value receiver. That means when you call it, the function gets a copy of the user. If we set the name to Alice, it only changes the copy — the original stays Bob.
Second method: SetNamePointer uses a pointer receiver. Here, we pass in the memory address, so the actual User object is modified. Now, when we print the name, it shows Alice as expected.
So the output is: Bob, then Alice.”

Why It’s Useful (1:20–2:10)
“Why does this matter? [pause] If your method is supposed to change the data, like updating a user’s profile, you must use a pointer receiver. Otherwise, nothing happens! [pause] On the flip side, if you just need to read data and don’t want to mutate it, a value receiver works fine. [pause] Knowing this difference is critical in interviews and real-world Go code.”

Outro (2:10–2:30)
“Have you ever been bitten by the pointer vs value receiver trap? [pause] Share your story in the comments — it might save someone else’s time. And if you found this breakdown helpful, give this video a thumbs up and subscribe for more Go interview prep tips!”