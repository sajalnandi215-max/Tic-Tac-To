let boxes=document.querySelectorAll(".box");
let reset=document.querySelector("#reset");
let new_btn=document.querySelector("#new_btn");
let msg=document.querySelector("#msg");
let msg_container=document.querySelector(".msg_container");
let turno=true;
const winpattern=[
    [0,1,2],
    [0,3,6],
    [0,4,8],
    [1,4,7],
    [2,5,8],
    [2,4,6],
    [3,4,5],
    [6,7,8],
];
const resetGame = () => {
    turno = true;
    enableBoxes();
    boxes.forEach((box) => {
        box.innerText = "";
    });
    msg_container.classList.add("hide");
};

boxes.forEach((box) => {
    box.addEventListener("click", () => {
        console.log("click");
        if(turno){
            box.innerText="O";
            turno=false;
        }else{
             box.innerText="X";
             turno=true;
        }
box.disabled=true;
        checkWinner();
    });
});
const disableBoxes=()=>{
    for(let box of boxes){
        box.disabled=true;
    }
}
const enableBoxes=()=>{
    for(let box of boxes){
        box.disabled=false;
    }
}
const show_winner=(winner) =>{
       msg.innerText=`${winner} is the winner`;
       msg_container.classList.remove("hide");
       disableBoxes();
}
 const checkWinner=()=>{
    for(let pattern of winpattern){
        // console.log(pattern[0],pattern[1],pattern[2]);
        // console.log( 
        //     boxes [pattern[0]].innerText,
        //     boxes [pattern[1]].innerText,
        //     boxes [pattern[2]].innerText);
        let post1val=boxes[pattern[0]].innerText;
        let post2val=boxes[pattern[1]].innerText;
        let post3val=boxes[pattern[2]].innerText;

        if(post1val !="" && post2val !="" && post3val !=""){
            if(post1val===post2val && post2val===post3val){
                console.log("winner",post1val);

                show_winner(post1val);

            }
        }
    }
 };
 new_btn.addEventListener("click",resetGame);
 reset.addEventListener("click",resetGame)
   