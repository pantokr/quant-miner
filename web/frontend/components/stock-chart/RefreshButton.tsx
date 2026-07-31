"use client";

import { Box, BoxProps, Icon } from "@chakra-ui/react";
import { RotateCw } from "lucide-react";

interface Props extends Omit<BoxProps, "onClick"> {
    onClick: () => void;
    /** 요청 중이면 아이콘이 돈다 */
    busy?: boolean;
}

/** 차트 위에 얹는 작은 새로고침 버튼 */
export function RefreshButton({ onClick, busy = false, ...rest }: Props) {
    return (
        <Box
            as="button"
            aria-label="새로고침"
            title="새로고침"
            onClick={onClick}
            // 차트 본체가 드래그/휠 이벤트를 받으므로 버튼에서는 전파를 끊는다
            onMouseDown={(e: React.MouseEvent) => e.stopPropagation()}
            display="inline-flex"
            alignItems="center"
            justifyContent="center"
            boxSize="24px"
            borderRadius="md"
            borderWidth="1px"
            borderColor="border.subtle"
            bg="bg.panel"
            color="fg.muted"
            cursor="pointer"
            transition="all 0.15s"
            _hover={{ color: "accent.500", borderColor: "accent.500" }}
            {...rest}
        >
            <Icon
                as={RotateCw}
                boxSize="3.5"
                animation={busy ? "qmSpin 0.8s linear infinite" : undefined}
            />
        </Box>
    );
}
