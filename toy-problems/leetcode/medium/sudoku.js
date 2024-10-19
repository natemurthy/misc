function boxSpot(i, j){
        return [3*Math.floor(i/3)+Math.floor(j/3), 3*(i%3)+(j%3)]
}

for (let i=0; i<9; i++) {
        console.log("")
        console.log(`---------${i}---------`)
        for (let j=0; j<9; j++) {
                console.log("spotR",i,j)
                console.log("spotC",j,i)
                console.log("boxSpot", boxSpot(i, j))
        }
}
