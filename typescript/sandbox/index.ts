let id: number = 5

console.log(id)

enum Direction1 {
    Up = 'Up',
    Down = 'Down',
    Left = 'Left',
    Right = 'Right'
}

console.log(Direction1.Up)

type User = {
    id: number,
    name: string
}

const user: User = {
    id: 0,
    name: 'John'
}

console.log(user)

// Type Assertion (two was of doing this)
let cid: any = 1

//let customerId = <number>cid
let customerId = cid as number

console.log(customerId)

function addNum(x: number, y: number) {
    return x + y
}

const user1: User = {id: 1, name: 'one'}
const user2: User = {id: 2, name: 'two'}

console.log(addNum(user1.id, user2.id))

// unions and void functions
function log(message: string | number): void {
    console.log(message)
}

// Interfaces
interface UserInterface {
    readonly id: number
    name: string
    age?: number // ? makes it optional
}

const user3: UserInterface = {
    id: 1,
    name: 'John'
}

interface MathFunc {
    (x: number, y: number): number
}

const add: MathFunc = (x: number, y: number): number => x + y