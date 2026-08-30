#include "WarSimCharacter.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AWarSimCharacter::AWarSimCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    GetCapsuleComponent()->InitCapsuleSize(34.f, 88.f);
    FirstPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
    FirstPersonCamera->SetupAttachment(GetCapsuleComponent());
    FirstPersonCamera->SetRelativeLocation(FVector(-8.f, 0.f, 64.f));
    FirstPersonCamera->bUsePawnControlRotation = true;
    GetCharacterMovement()->MaxWalkSpeed = 360.f;
}

void AWarSimCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis("MoveForward", this, &AWarSimCharacter::MoveForward);
    Input->BindAxis("MoveRight", this, &AWarSimCharacter::MoveRight);
    Input->BindAxis("Turn", this, &AWarSimCharacter::Turn);
    Input->BindAxis("LookUp", this, &AWarSimCharacter::LookUp);
}
void AWarSimCharacter::MoveForward(float V){ if(FMath::Abs(V)>KINDA_SMALL_NUMBER) AddMovementInput(GetActorForwardVector(),V); }
void AWarSimCharacter::MoveRight(float V){ if(FMath::Abs(V)>KINDA_SMALL_NUMBER) AddMovementInput(GetActorRightVector(),V); }
void AWarSimCharacter::Turn(float V){ AddControllerYawInput(V); }
void AWarSimCharacter::LookUp(float V){ AddControllerPitchInput(V); }
