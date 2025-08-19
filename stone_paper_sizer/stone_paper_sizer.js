let user_sscore = 0;
let com_sscore = 0;

const icon_section = document.querySelectorAll(".icon");
const user_score = document.querySelector("#user_score");
const com_score = document.querySelector("#com_score");
const inerText= document.querySelector("#inner");


icon_section.forEach((icon) => {
  icon.addEventListener("click", () => {
    const user_choice=icon.id
    play_game(user_choice);
  });
});


const play_game = (user_choice) => {
      console.log("User choice:", user_choice);
      const com_choice_value = com_choice();
      console.log("Computer choice:", com_choice_value);
      if (user_choice === com_choice_value) {
        console.log("It's a tie!");
        inerText.innerText = `You chose ${user_choice} and computer chose ${com_choice_value}. It's a tie!`;    
      }else if((user_choice === "stone" && com_choice_value === "scissor") ||
                (user_choice === "paper" && com_choice_value === "stone") ||
                (user_choice === "scissor" && com_choice_value === "paper")) {
        console.log("User wins!");
        user_sscore++;
        user_score.innerText = user_sscore;
        inerText.innerText = `You chose ${user_choice} and computer chose ${com_choice_value}. You win!`;
        
      }else {
        console.log("Computer wins!");
        com_sscore++;
        com_score.innerText = com_sscore;
        inerText.innerText = `You chose ${user_choice} and computer chose ${com_choice_value}. Computer wins!`;
       
      }
}



const com_choice =()=>{
    const choices=["stone", "paper", "scissor"];
    // console.log(choices)
    const random_index= Math.floor(Math.random() * choices.length);
    // const com_choice = choices[Math.floor(Math.random() * choices.length)];
    const selected= choices[random_index];
    // console.log("Computer choice:", selected);
    return selected;
    
}

