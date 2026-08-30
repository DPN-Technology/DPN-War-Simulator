ERAS = {
    "Ancient Era": [
        "Roman Empire", "Greek Wars", "Persian Wars", "Punic Wars", "Viking Age",
        "Medieval Europe", "Mongol Expansion", "Samurai Era", "Crusades",
    ],
    "Age of Sail": [
        "Napoleonic Wars", "American Revolution", "War of 1812",
        "Colonial Naval Warfare", "Pirate Era",
    ],
    "Industrial Era": ["American Civil War", "Franco-Prussian War", "Russo-Japanese War"],
    "World War I": ["Every major front", "Major naval battles", "Major air campaigns"],
    "World War II": [
        "Pacific Theater", "European Theater", "African Campaign", "Atlantic Convoys",
        "Strategic Bombing", "Island Hopping", "Carrier Warfare", "Submarine Warfare",
        "Battle of Midway", "Pearl Harbor", "Battle of the Atlantic", "Normandy",
        "Iwo Jima", "Guadalcanal", "Leyte Gulf", "Battle of Britain", "Ardennes", "Berlin",
    ],
    "Cold War": ["Korean War", "Vietnam War", "Cuban Missile Crisis", "Naval Standoffs", "Special Operations"],
    "Modern Era": [
        "Gulf War", "Afghanistan", "Iraq", "Counterterrorism Operations",
        "Modern Naval Warfare", "Drone Warfare", "Cyber Operations", "Space Operations",
    ],
}

BRANCHES = ["Navy", "Army", "Marine Corps", "Air Force", "Coast Guard", "Merchant Marine", "Historical Branch"]

NAVAL_RANKS = [
    "Recruit", "Seaman Recruit", "Seaman Apprentice", "Seaman", "Petty Officer",
    "Chief", "Senior Chief", "Master Chief", "Warrant Officer", "Ensign",
    "Lieutenant Junior Grade", "Lieutenant", "Lieutenant Commander", "Commander",
    "Captain", "Rear Admiral", "Vice Admiral", "Admiral", "Fleet Admiral",
]

HELM_TOPICS = [
    "Steering", "Navigation", "Collision Avoidance", "Emergency Procedures",
    "Damage Response", "Anchoring", "Formation Maneuvering", "Night Operations",
    "Heavy Weather Operations",
]

CAPTAIN_DEPARTMENTS = [
    "Navigation", "Engineering", "Combat", "Medical", "Communications", "Supply",
    "Leadership", "Damage Control", "Aviation", "Weapons", "Fire Control",
    "Nuclear Operations", "Administration", "Logistics",
]

PROMOTION_REQUIREMENTS = {
    "Testing": 70,
    "Practical examinations": 70,
    "Performance reviews": 65,
    "Leadership evaluations": 50,
    "Recommendations": 1,
    "Training schools": 1,
    "Time in service": 3,
    "Experience": 300,
    "Mission performance": 65,
}

WRITTEN_QUESTIONS = [
    {
        "q": "Which action best reflects collision avoidance before changing course?",
        "choices": ["Check traffic and relative motion", "Increase speed immediately", "Ignore visibility", "Secure steering"],
        "answer": 0,
        "topic": "Collision Avoidance",
    },
    {
        "q": "In heavy weather, what should a helmsman expect?",
        "choices": ["No effect on steering", "Course corrections may be more frequent", "Navigation becomes unnecessary", "Rudder is never used"],
        "answer": 1,
        "topic": "Heavy Weather Operations",
    },
    {
        "q": "If steering response becomes abnormal, what is the best first principle?",
        "choices": ["Hide the problem", "Report it and follow emergency steering procedure", "Abandon station", "Increase speed"],
        "answer": 1,
        "topic": "Emergency Procedures",
    },
    {
        "q": "Why does night operation require added care?",
        "choices": ["Reduced visual references", "The rudder stops working", "Compasses cannot be used", "Waves disappear"],
        "answer": 0,
        "topic": "Night Operations",
    },
    {
        "q": "What does a heading order require from the helmsman?",
        "choices": ["Hold the ordered course accurately", "Choose any course", "Stop reporting", "Use maximum rudder at all times"],
        "answer": 0,
        "topic": "Steering",
    },
    {
        "q": "What is a key purpose of navigation information on the bridge?",
        "choices": ["Track safe movement and position", "Decorate the display", "Replace communications", "Eliminate weather"],
        "answer": 0,
        "topic": "Navigation",
    },
    {
        "q": "During formation maneuvering, the helmsman should prioritize:",
        "choices": ["Station keeping and ordered movements", "Independent maneuvering", "Maximum speed", "Ignoring nearby ships"],
        "answer": 0,
        "topic": "Formation Maneuvering",
    },
    {
        "q": "During anchoring, steering actions should be:",
        "choices": ["Coordinated with bridge orders", "Random", "Delayed intentionally", "Made without reports"],
        "answer": 0,
        "topic": "Anchoring",
    },
    {
        "q": "If damage affects the ship's ability to maneuver, the helmsman should:",
        "choices": ["Continue silently", "Report changes and execute damage-response steering orders", "Leave the bridge", "Disable communications"],
        "answer": 1,
        "topic": "Damage Response",
    },
    {
        "q": "Which combination best supports realistic bridge performance?",
        "choices": ["Training, communication, discipline", "Guessing, speed, shortcuts", "Perfect information", "Automatic promotion"],
        "answer": 0,
        "topic": "Steering",
    },
]

CREW_NAMES = [
    "Alex Mercer", "Jordan Hale", "Morgan Reed", "Taylor Brooks", "Casey Warren",
    "Riley Stone", "Avery Cole", "Parker Shaw", "Drew Bennett", "Cameron Ellis",
    "Logan Hayes", "Quinn Foster", "Hayden Grant", "Reese Morgan", "Blake Turner",
]
