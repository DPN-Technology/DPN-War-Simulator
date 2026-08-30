#include "CV6WatertightDoorActor.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"

ACV6WatertightDoorActor::ACV6WatertightDoorActor()
{
    PrimaryActorTick.bCanEverTick = true;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    SetRootComponent(Root);
    FrameMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Frame"));
    FrameMesh->SetupAttachment(Root);
    DoorMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Door"));
    DoorMesh->SetupAttachment(Root);
    DoorMesh->SetMobility(EComponentMobility::Movable);
}

void ACV6WatertightDoorActor::ToggleDoor(){ if(!bLocked) SetDoorOpen(!bIsOpen); }
void ACV6WatertightDoorActor::SetDoorOpen(bool bOpen)
{
    if(bLocked && bOpen) return;
    bIsOpen=bOpen; TargetYaw=bIsOpen ? OpenAngleDeg : 0.f;
}
void ACV6WatertightDoorActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    FRotator R=DoorMesh->GetRelativeRotation();
    R.Yaw=FMath::FInterpConstantTo(R.Yaw,TargetYaw,DeltaSeconds,OpenSpeedDegPerSec);
    DoorMesh->SetRelativeRotation(R);
    DoorMesh->SetCollisionEnabled(FMath::Abs(R.Yaw) < 70.f ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::QueryOnly);
}
